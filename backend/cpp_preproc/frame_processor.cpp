/**
 * Frame Processor Implementation
 */

#include "frame_processor.hpp"
#include <algorithm>
#include <stdexcept>
#include <cstring>

namespace overwatch {

FrameProcessor::FrameProcessor(int num_threads)
    : num_threads_(num_threads > 0 ? num_threads : std::thread::hardware_concurrency()),
      frames_processed_(0),
      bytes_encoded_(0) {
    
    // Initialize turbojpeg compressor
    jpeg_compressor_ = tjInitCompress();
    if (!jpeg_compressor_) {
        throw std::runtime_error("Failed to initialize turbojpeg compressor");
    }
}

FrameProcessor::~FrameProcessor() {
    if (jpeg_compressor_) {
        tjDestroy(jpeg_compressor_);
    }
}

ProcessedFrame FrameProcessor::resize_frame(
    const cv::Mat& frame,
    int width,
    int height,
    int interpolation
) {
    ProcessedFrame result;
    result.width = width;
    result.height = height;
    result.channels = frame.channels();
    result.success = true;

    try {
        cv::Mat resized;
        cv::resize(frame, resized, cv::Size(width, height), 0, 0, interpolation);
        
        // Convert to contiguous buffer
        size_t data_size = resized.total() * resized.elemSize();
        result.data.resize(data_size);
        std::memcpy(result.data.data(), resized.data, data_size);
        
        std::lock_guard<std::mutex> lock(stats_mutex_);
        frames_processed_++;
        
    } catch (const std::exception& e) {
        result.success = false;
        result.error_msg = e.what();
    }

    return result;
}

cv::Mat FrameProcessor::preprocess_internal(const cv::Mat& frame, const PreprocessConfig& config) {
    cv::Mat processed = frame.clone();

    // Resize
    if (config.target_width > 0 && config.target_height > 0) {
        cv::resize(processed, processed, 
                   cv::Size(config.target_width, config.target_height),
                   0, 0, config.interpolation);
    }

    // Color conversion BGR -> RGB
    if (config.rgb_conversion && frame.channels() == 3) {
        cv::cvtColor(processed, processed, cv::COLOR_BGR2RGB);
    }

    // Normalize
    if (config.normalize) {
        // Convert to float32
        processed.convertTo(processed, CV_32FC3, 1.0 / 255.0);
        
        // Apply mean/std normalization if provided
        if (config.mean[0] != 0.0f || config.mean[1] != 0.0f || config.mean[2] != 0.0f ||
            config.std[0] != 1.0f || config.std[1] != 1.0f || config.std[2] != 1.0f) {
            
            std::vector<cv::Mat> channels;
            cv::split(processed, channels);
            
            for (int i = 0; i < 3; i++) {
                channels[i] = (channels[i] - config.mean[i]) / config.std[i];
            }
            
            cv::merge(channels, processed);
        }
    }

    return processed;
}

ProcessedFrame FrameProcessor::preprocess_for_inference(
    const cv::Mat& frame,
    const PreprocessConfig& config
) {
    ProcessedFrame result;
    result.success = true;

    try {
        cv::Mat processed = preprocess_internal(frame, config);
        
        result.width = processed.cols;
        result.height = processed.rows;
        result.channels = processed.channels();
        
        // Convert to contiguous buffer
        size_t data_size = processed.total() * processed.elemSize();
        result.data.resize(data_size);
        std::memcpy(result.data.data(), processed.data, data_size);
        
        std::lock_guard<std::mutex> lock(stats_mutex_);
        frames_processed_++;
        
    } catch (const std::exception& e) {
        result.success = false;
        result.error_msg = e.what();
    }

    return result;
}

std::vector<ProcessedFrame> FrameProcessor::batch_preprocess(
    const std::vector<cv::Mat>& frames,
    const PreprocessConfig& config
) {
    std::vector<ProcessedFrame> results;
    results.reserve(frames.size());

    // Process frames in parallel using OpenMP if available
    #pragma omp parallel for num_threads(num_threads_)
    for (size_t i = 0; i < frames.size(); i++) {
        ProcessedFrame result = preprocess_for_inference(frames[i], config);
        
        #pragma omp critical
        results.push_back(std::move(result));
    }

    return results;
}

ProcessedFrame FrameProcessor::encode_jpeg_internal(
    const cv::Mat& frame,
    const JPEGConfig& config
) {
    ProcessedFrame result;
    result.width = frame.cols;
    result.height = frame.rows;
    result.channels = frame.channels();
    result.success = true;

    try {
        // Ensure frame is in BGR format (OpenCV default)
        cv::Mat bgr_frame = frame;
        if (frame.channels() == 4) {
            cv::cvtColor(frame, bgr_frame, cv::COLOR_BGRA2BGR);
        }

        // Determine pixel format
        int pixel_format = TJPF_BGR;
        int channels = bgr_frame.channels();
        
        if (channels == 1) {
            pixel_format = TJPF_GRAY;
        } else if (channels == 3) {
            pixel_format = TJPF_BGR;
        } else {
            throw std::runtime_error("Unsupported channel count");
        }

        // Prepare output buffer
        unsigned char* jpeg_buf = nullptr;
        unsigned long jpeg_size = 0;

        // Compress using turbojpeg
        int ret = tjCompress2(
            jpeg_compressor_,
            bgr_frame.data,
            bgr_frame.cols,
            bgr_frame.step,  // pitch (bytes per line)
            bgr_frame.rows,
            pixel_format,
            &jpeg_buf,
            &jpeg_size,
            config.subsample,
            config.quality,
            config.optimize ? TJFLAG_FASTDCT : 0
        );

        if (ret != 0) {
            throw std::runtime_error(std::string("turbojpeg compression failed: ") + tjGetErrorStr());
        }

        // Copy to result
        result.data.resize(jpeg_size);
        std::memcpy(result.data.data(), jpeg_buf, jpeg_size);
        
        // Free turbojpeg buffer
        tjFree(jpeg_buf);

        std::lock_guard<std::mutex> lock(stats_mutex_);
        frames_processed_++;
        bytes_encoded_ += jpeg_size;

    } catch (const std::exception& e) {
        result.success = false;
        result.error_msg = e.what();
    }

    return result;
}

ProcessedFrame FrameProcessor::encode_jpeg(
    const cv::Mat& frame,
    const JPEGConfig& config
) {
    return encode_jpeg_internal(frame, config);
}

std::vector<ProcessedFrame> FrameProcessor::batch_encode_jpeg(
    const std::vector<cv::Mat>& frames,
    const JPEGConfig& config
) {
    std::vector<ProcessedFrame> results(frames.size());

    // Each thread needs its own turbojpeg handle
    #pragma omp parallel num_threads(num_threads_)
    {
        tjhandle compressor = tjInitCompress();
        
        #pragma omp for
        for (size_t i = 0; i < frames.size(); i++) {
            results[i] = encode_jpeg_internal(frames[i], config);
        }
        
        tjDestroy(compressor);
    }

    return results;
}

ProcessedFrame FrameProcessor::preprocess_and_encode(
    const cv::Mat& frame,
    const PreprocessConfig& preproc_config,
    const JPEGConfig& jpeg_config
) {
    try {
        // Preprocess
        cv::Mat processed = preprocess_internal(frame, preproc_config);
        
        // Encode
        return encode_jpeg_internal(processed, jpeg_config);
        
    } catch (const std::exception& e) {
        ProcessedFrame result;
        result.success = false;
        result.error_msg = e.what();
        return result;
    }
}

cv::Mat FrameProcessor::bgr_to_rgb(const cv::Mat& frame) {
    cv::Mat rgb;
    cv::cvtColor(frame, rgb, cv::COLOR_BGR2RGB);
    return rgb;
}

cv::Mat FrameProcessor::rgb_to_bgr(const cv::Mat& frame) {
    cv::Mat bgr;
    cv::cvtColor(frame, bgr, cv::COLOR_RGB2BGR);
    return bgr;
}

cv::Mat FrameProcessor::normalize_frame(
    const cv::Mat& frame,
    const float mean[3],
    const float std[3]
) {
    cv::Mat normalized;
    frame.convertTo(normalized, CV_32FC3, 1.0 / 255.0);
    
    std::vector<cv::Mat> channels;
    cv::split(normalized, channels);
    
    for (int i = 0; i < std::min(3, (int)channels.size()); i++) {
        channels[i] = (channels[i] - mean[i]) / std[i];
    }
    
    cv::merge(channels, normalized);
    return normalized;
}

void FrameProcessor::reset_stats() {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    frames_processed_ = 0;
    bytes_encoded_ = 0;
}

// FrameProcessorPool implementation
FrameProcessorPool::FrameProcessorPool(size_t num_threads)
    : stop_(false) {
    
    for (size_t i = 0; i < num_threads; i++) {
        workers_.emplace_back(&FrameProcessorPool::worker_thread, this);
    }
}

FrameProcessorPool::~FrameProcessorPool() {
    shutdown();
}

void FrameProcessorPool::worker_thread() {
    while (true) {
        std::function<void()> task;
        
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            condition_.wait(lock, [this] { return stop_ || !tasks_.empty(); });
            
            if (stop_ && tasks_.empty()) {
                return;
            }
            
            task = std::move(tasks_.front());
            tasks_.pop();
        }
        
        task();
    }
}

std::future<std::vector<ProcessedFrame>> FrameProcessorPool::submit_batch(
    const std::vector<cv::Mat>& frames,
    const PreprocessConfig& config
) {
    auto promise = std::make_shared<std::promise<std::vector<ProcessedFrame>>>();
    auto future = promise->get_future();
    
    {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        
        tasks_.emplace([frames, config, promise]() {
            FrameProcessor processor;
            auto results = processor.batch_preprocess(frames, config);
            promise->set_value(std::move(results));
        });
    }
    
    condition_.notify_one();
    return future;
}

std::future<std::vector<ProcessedFrame>> FrameProcessorPool::submit_encode_batch(
    const std::vector<cv::Mat>& frames,
    const JPEGConfig& config
) {
    auto promise = std::make_shared<std::promise<std::vector<ProcessedFrame>>>();
    auto future = promise->get_future();
    
    {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        
        tasks_.emplace([frames, config, promise]() {
            FrameProcessor processor;
            auto results = processor.batch_encode_jpeg(frames, config);
            promise->set_value(std::move(results));
        });
    }
    
    condition_.notify_one();
    return future;
}

void FrameProcessorPool::shutdown() {
    {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        stop_ = true;
    }
    
    condition_.notify_all();
    
    for (auto& worker : workers_) {
        if (worker.joinable()) {
            worker.join();
        }
    }
}

} // namespace overwatch

