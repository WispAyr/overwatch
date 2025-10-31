/**
 * Python bindings for frame_processor using pybind11
 */

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "frame_processor.hpp"

namespace py = pybind11;

namespace overwatch {

// Convert numpy array to cv::Mat (zero-copy view)
cv::Mat numpy_to_mat(py::array_t<uint8_t> input) {
    py::buffer_info buf = input.request();
    
    if (buf.ndim == 2) {
        // Grayscale
        return cv::Mat(buf.shape[0], buf.shape[1], CV_8UC1, buf.ptr);
    } else if (buf.ndim == 3) {
        // Color (assume BGR)
        return cv::Mat(buf.shape[0], buf.shape[1], CV_8UC3, buf.ptr);
    } else {
        throw std::runtime_error("Unsupported array dimensions");
    }
}

// Convert cv::Mat to numpy array (zero-copy if possible)
py::array_t<uint8_t> mat_to_numpy(const cv::Mat& mat) {
    std::vector<py::ssize_t> shape;
    std::vector<py::ssize_t> strides;
    
    if (mat.channels() == 1) {
        shape = {mat.rows, mat.cols};
        strides = {mat.step, sizeof(uint8_t)};
    } else {
        shape = {mat.rows, mat.cols, mat.channels()};
        strides = {mat.step, mat.channels() * sizeof(uint8_t), sizeof(uint8_t)};
    }
    
    return py::array_t<uint8_t>(shape, strides, mat.data);
}

// Convert ProcessedFrame to numpy array or bytes
py::object processed_frame_to_python(const ProcessedFrame& frame) {
    if (!frame.success) {
        throw std::runtime_error(frame.error_msg);
    }
    
    // Return as bytes (for JPEG encoded data) or numpy array
    return py::bytes(reinterpret_cast<const char*>(frame.data.data()), frame.data.size());
}

// Wrapper functions for Python
class PyFrameProcessor {
public:
    PyFrameProcessor(int num_threads = 0) : processor_(num_threads) {}
    
    py::bytes encode_jpeg(py::array_t<uint8_t> frame, int quality = 85) {
        cv::Mat mat = numpy_to_mat(frame);
        
        JPEGConfig config;
        config.quality = quality;
        
        ProcessedFrame result = processor_.encode_jpeg(mat, config);
        
        if (!result.success) {
            throw std::runtime_error(result.error_msg);
        }
        
        return py::bytes(reinterpret_cast<const char*>(result.data.data()), result.data.size());
    }
    
    std::vector<py::bytes> batch_encode_jpeg(std::vector<py::array_t<uint8_t>> frames, int quality = 85) {
        // Convert numpy arrays to cv::Mat
        std::vector<cv::Mat> mats;
        mats.reserve(frames.size());
        for (auto& frame : frames) {
            mats.push_back(numpy_to_mat(frame));
        }
        
        JPEGConfig config;
        config.quality = quality;
        
        auto results = processor_.batch_encode_jpeg(mats, config);
        
        // Convert results to Python bytes
        std::vector<py::bytes> py_results;
        py_results.reserve(results.size());
        for (auto& result : results) {
            if (!result.success) {
                throw std::runtime_error(result.error_msg);
            }
            py_results.push_back(
                py::bytes(reinterpret_cast<const char*>(result.data.data()), result.data.size())
            );
        }
        
        return py_results;
    }
    
    py::array_t<uint8_t> resize_frame(py::array_t<uint8_t> frame, int width, int height) {
        cv::Mat mat = numpy_to_mat(frame);
        
        ProcessedFrame result = processor_.resize_frame(mat, width, height);
        
        if (!result.success) {
            throw std::runtime_error(result.error_msg);
        }
        
        // Reconstruct cv::Mat from result data
        int type = result.channels == 1 ? CV_8UC1 : CV_8UC3;
        cv::Mat output(result.height, result.width, type, result.data.data());
        
        return mat_to_numpy(output);
    }
    
    py::array_t<uint8_t> bgr_to_rgb(py::array_t<uint8_t> frame) {
        cv::Mat mat = numpy_to_mat(frame);
        cv::Mat rgb = processor_.bgr_to_rgb(mat);
        return mat_to_numpy(rgb);
    }
    
    py::array_t<uint8_t> rgb_to_bgr(py::array_t<uint8_t> frame) {
        cv::Mat mat = numpy_to_mat(frame);
        cv::Mat bgr = processor_.rgb_to_bgr(mat);
        return mat_to_numpy(bgr);
    }
    
    py::dict preprocess_for_inference(
        py::array_t<uint8_t> frame,
        int target_width,
        int target_height,
        bool normalize = true,
        bool rgb_conversion = true
    ) {
        cv::Mat mat = numpy_to_mat(frame);
        
        PreprocessConfig config;
        config.target_width = target_width;
        config.target_height = target_height;
        config.normalize = normalize;
        config.rgb_conversion = rgb_conversion;
        
        ProcessedFrame result = processor_.preprocess_for_inference(mat, config);
        
        if (!result.success) {
            throw std::runtime_error(result.error_msg);
        }
        
        // Return as dict with metadata
        py::dict output;
        
        if (normalize) {
            // Return float32 array
            cv::Mat float_mat(result.height, result.width, CV_32FC3, (void*)result.data.data());
            
            std::vector<py::ssize_t> shape = {result.height, result.width, result.channels};
            std::vector<py::ssize_t> strides = {
                result.width * result.channels * sizeof(float),
                result.channels * sizeof(float),
                sizeof(float)
            };
            
            output["data"] = py::array_t<float>(shape, strides, (float*)result.data.data());
        } else {
            cv::Mat output_mat(result.height, result.width, CV_8UC3, (void*)result.data.data());
            output["data"] = mat_to_numpy(output_mat);
        }
        
        output["width"] = result.width;
        output["height"] = result.height;
        output["channels"] = result.channels;
        
        return output;
    }
    
    size_t get_frames_processed() const { return processor_.get_frames_processed(); }
    size_t get_bytes_encoded() const { return processor_.get_bytes_encoded(); }
    void reset_stats() { processor_.reset_stats(); }
    
private:
    FrameProcessor processor_;
};

} // namespace overwatch

PYBIND11_MODULE(frame_processor, m) {
    m.doc() = "Fast C++ frame preprocessing for Overwatch";
    
    py::class_<overwatch::PyFrameProcessor>(m, "FrameProcessor")
        .def(py::init<int>(), py::arg("num_threads") = 0,
             "Create frame processor with specified thread count (0 = auto)")
        
        // JPEG encoding
        .def("encode_jpeg", &overwatch::PyFrameProcessor::encode_jpeg,
             py::arg("frame"), py::arg("quality") = 85,
             "Encode frame to JPEG using turbojpeg (2-6x faster than cv2.imencode)")
        
        .def("batch_encode_jpeg", &overwatch::PyFrameProcessor::batch_encode_jpeg,
             py::arg("frames"), py::arg("quality") = 85,
             "Batch encode multiple frames to JPEG in parallel")
        
        // Preprocessing
        .def("resize_frame", &overwatch::PyFrameProcessor::resize_frame,
             py::arg("frame"), py::arg("width"), py::arg("height"),
             "Resize frame to target dimensions")
        
        .def("preprocess_for_inference", &overwatch::PyFrameProcessor::preprocess_for_inference,
             py::arg("frame"),
             py::arg("target_width"),
             py::arg("target_height"),
             py::arg("normalize") = true,
             py::arg("rgb_conversion") = true,
             "Preprocess frame for AI inference (resize, normalize, color convert)")
        
        // Color conversion
        .def("bgr_to_rgb", &overwatch::PyFrameProcessor::bgr_to_rgb,
             py::arg("frame"),
             "Convert BGR to RGB")
        
        .def("rgb_to_bgr", &overwatch::PyFrameProcessor::rgb_to_bgr,
             py::arg("frame"),
             "Convert RGB to BGR")
        
        // Stats
        .def("get_frames_processed", &overwatch::PyFrameProcessor::get_frames_processed,
             "Get total frames processed")
        
        .def("get_bytes_encoded", &overwatch::PyFrameProcessor::get_bytes_encoded,
             "Get total bytes encoded (JPEG)")
        
        .def("reset_stats", &overwatch::PyFrameProcessor::reset_stats,
             "Reset statistics counters");
}

