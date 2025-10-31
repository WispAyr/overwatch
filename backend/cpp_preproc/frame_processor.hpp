/**
 * Fast Frame Preprocessing for Overwatch
 * 
 * High-performance C++ preprocessing pipeline that bypasses Python GIL
 * for multi-camera frame operations.
 */

#ifndef FRAME_PROCESSOR_HPP
#define FRAME_PROCESSOR_HPP

#include <opencv2/opencv.hpp>
#include <turbojpeg.h>
#include <vector>
#include <memory>
#include <thread>
#include <future>
#include <queue>
#include <mutex>
#include <condition_variable>

namespace overwatch {

/**
 * Frame preprocessing operations
 */
struct PreprocessConfig {
    int target_width = 640;
    int target_height = 640;
    bool normalize = true;        // Normalize to [0, 1]
    bool rgb_conversion = true;   // Convert BGR to RGB
    float mean[3] = {0.0f, 0.0f, 0.0f};
    float std[3] = {1.0f, 1.0f, 1.0f};
    int interpolation = cv::INTER_LINEAR;
};

/**
 * JPEG encoding configuration
 */
struct JPEGConfig {
    int quality = 85;
    int subsample = TJSAMP_420;  // 4:2:0 chroma subsampling
    bool optimize = true;
    bool progressive = false;
};

/**
 * Batch frame result
 */
struct ProcessedFrame {
    std::vector<uint8_t> data;      // Processed/encoded data
    int width;
    int height;
    int channels;
    bool success;
    std::string error_msg;
};

/**
 * Multi-threaded frame processor
 */
class FrameProcessor {
public:
    FrameProcessor(int num_threads = 0);
    ~FrameProcessor();

    // Preprocessing operations
    ProcessedFrame resize_frame(const cv::Mat& frame, int width, int height, int interpolation = cv::INTER_LINEAR);
    
    ProcessedFrame preprocess_for_inference(const cv::Mat& frame, const PreprocessConfig& config);
    
    std::vector<ProcessedFrame> batch_preprocess(
        const std::vector<cv::Mat>& frames,
        const PreprocessConfig& config
    );

    // JPEG encoding operations
    ProcessedFrame encode_jpeg(const cv::Mat& frame, const JPEGConfig& config);
    
    std::vector<ProcessedFrame> batch_encode_jpeg(
        const std::vector<cv::Mat>& frames,
        const JPEGConfig& config
    );

    // Combined operations (preprocess + encode)
    ProcessedFrame preprocess_and_encode(
        const cv::Mat& frame,
        const PreprocessConfig& preproc_config,
        const JPEGConfig& jpeg_config
    );

    // Color space conversions
    cv::Mat bgr_to_rgb(const cv::Mat& frame);
    cv::Mat rgb_to_bgr(const cv::Mat& frame);

    // Normalization
    cv::Mat normalize_frame(const cv::Mat& frame, const float mean[3], const float std[3]);

    // Stats
    size_t get_frames_processed() const { return frames_processed_; }
    size_t get_bytes_encoded() const { return bytes_encoded_; }
    void reset_stats();

private:
    tjhandle jpeg_compressor_;
    int num_threads_;
    size_t frames_processed_;
    size_t bytes_encoded_;
    std::mutex stats_mutex_;

    // Helper methods
    ProcessedFrame encode_jpeg_internal(const cv::Mat& frame, const JPEGConfig& config);
    cv::Mat preprocess_internal(const cv::Mat& frame, const PreprocessConfig& config);
};

/**
 * Thread pool for parallel frame processing
 */
class FrameProcessorPool {
public:
    FrameProcessorPool(size_t num_threads);
    ~FrameProcessorPool();

    // Submit batch processing job
    std::future<std::vector<ProcessedFrame>> submit_batch(
        const std::vector<cv::Mat>& frames,
        const PreprocessConfig& config
    );

    // Submit batch JPEG encoding job
    std::future<std::vector<ProcessedFrame>> submit_encode_batch(
        const std::vector<cv::Mat>& frames,
        const JPEGConfig& config
    );

    void shutdown();

private:
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex queue_mutex_;
    std::condition_variable condition_;
    bool stop_;

    void worker_thread();
};

} // namespace overwatch

#endif // FRAME_PROCESSOR_HPP

