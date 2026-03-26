"""
EVM (Eulerian Video Magnification) based Heart Rate Detection for CCTV
Handles low resolution, compression, motion, and variable lighting
"""

import numpy as np
import time
from scipy.signal import butter, filtfilt, find_peaks
from scipy.fft import fft, fftfreq
from scipy.interpolate import interp1d
from collections import deque
import cv2

class EVMProcessor:
    def __init__(
        self,
        fs=30,  # Frame rate
        bpm_min=70,  # Minimum BPM
        bpm_max=130,  # Maximum BPM
        buffer_seconds=10,  # Buffer size
        debug=False
    ):
        self.fs = fs  # Sampling frequency (frames per second)
        self.bpm_min = bpm_min
        self.bpm_max = bpm_max
        
        # Convert BPM to Hz
        self.freq_low = bpm_min / 60.0  # Hz
        self.freq_high = bpm_max / 60.0  # Hz
        
        # Buffer for signal processing
        self.buffer_size = int(fs * buffer_seconds)
        self.signal_buffer = deque(maxlen=self.buffer_size)
        self.time_buffer = deque(maxlen=self.buffer_size)
        
        # BPM tracking
        self.current_bpm = None
        self.smoothed_bpm = None
        self.confidence = "LOW"
        
        # Timing
        self.last_update_time = time.time()
        self.update_interval = 1.0  # Update BPM every 2 seconds
        
        # Debug
        self.debug = debug
        self.signal_history = []
        self.fft_debug_history = []
        
        # Signal quality tracking
        self.last_valid_bpm_time = 0
        self.consecutive_failures = 0
        self.bpm_history = deque(maxlen=20)  # Store last 20 BPM readings
        
        if self.debug:
            print(f"[EVM] Initialized with BPM range: {bpm_min}-{bpm_max} BPM")
            print(f"[EVM] Frequency range: {self.freq_low:.3f}-{self.freq_high:.3f} Hz")
            print(f"[EVM] Buffer: {self.buffer_size} samples ({buffer_seconds} seconds)")
            print(f"[EVM] Update interval: {self.update_interval} seconds")

    def _detect_respiratory_modulation(self, signal, fs):
     if len(signal) < fs * 5:  # need ~5 seconds minimum
        return 0.0

     try:
        # 1. Amplitude envelope via absolute + smoothing
        envelope = np.abs(signal)
        envelope = envelope - np.mean(envelope)

        # Smooth envelope (low-pass)
        win = int(fs * 0.8)  # ~0.8s window
        if win < 3:
            win = 3
        kernel = np.ones(win) / win
        envelope_smooth = np.convolve(envelope, kernel, mode="same")

        # 2. FFT of envelope
        n = len(envelope_smooth)
        freqs = fftfreq(n, 1 / fs)
        fft_env = np.abs(fft(envelope_smooth))

        # Positive frequencies only
        mask = freqs > 0
        freqs = freqs[mask]
        fft_env = fft_env[mask]

        # 3. Respiratory band (0.1–0.3 Hz)
        resp_mask = (freqs >= 0.1) & (freqs <= 0.3)
        if not np.any(resp_mask):
            return 0.0

        resp_energy = np.sum(fft_env[resp_mask])
        total_energy = np.sum(fft_env)

        if total_energy <= 0:
            return 0.0

        respiration_score = resp_energy / total_energy
        return respiration_score

     except Exception as e:
        if self.debug:
            print(f"[RSA ERROR] {e}")
        return 0.0

    def _adjust_brightness(self, roi):
        """Adjust ROI brightness for better detection using LAB color space"""
        if roi is None or roi.size == 0:
            return roi
            
        try:
            # Convert to LAB
            lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Increase lightness if too dark
            l_mean = np.mean(l)
            if l_mean < 80:  # Too dark
                l = cv2.add(l, 40)
                lab = cv2.merge([l, a, b])
                roi = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            return roi
        except Exception as e:
            if self.debug:
                print(f"[BRIGHTNESS ERROR] {e}")
            return roi

    def _extract_green_signal(self, roi):
        """
        Extract green channel signal from ROI
        For CCTV: Green channel is most robust to compression
        Uses weighted approach for center pixels (higher blood flow signal)
        """
        if roi is None or roi.size == 0:
            return None
        
        try:
            h, w = roi.shape[:2]
            
            # Create Gaussian weight map (center weighted)
            y, x = np.ogrid[:h, :w]
            center_y, center_x = h // 2, w // 2
            sigma = min(h, w) / 3.0
            weights = np.exp(-((x - center_x)**2 + (y - center_y)**2) / (2 * sigma**2))
            weights = weights / np.max(weights)  # Normalize
            
            # Extract green channel
            green = roi[:, :, 1].astype(np.float32)
            
            # Calculate weighted mean
            weighted_green = np.sum(green * weights) / np.sum(weights)
            
            # Also calculate unweighted for fallback
            unweighted_green = np.mean(green)
            
            # Use weighted if it has good variation, else unweighted
            weighted_std = np.std(green * weights)
            unweighted_std = np.std(green)
            
            if weighted_std > unweighted_std * 0.5:
                signal_value = weighted_green
            else:
                signal_value = np.mean(green) * 4.0
            
            return signal_value
            
        except Exception as e:
            if self.debug:
                print(f"[GREEN SIGNAL ERROR] {e}")
            return None

    def _bandpass_filter(self, signal, fs):
        """Apply bandpass filter for heart rate frequencies"""
        try:
            nyquist = 0.5 * fs
            low = self.freq_low / nyquist
            high = self.freq_high / nyquist
            
            if self.debug and len(self.signal_buffer) % 120 == 0:
                print(f"[FILTER] FS: {fs:.1f} Hz, Range: {self.freq_low:.3f}-{self.freq_high:.3f} Hz")
            
            # Ensure frequencies are valid
            if low >= 1 or high >= 1 or low >= high:
                if self.debug:
                    print(f"[FILTER WARNING] Invalid frequencies: low={low:.3f}, high={high:.3f}")
                return signal
            
            b, a = butter(3, [low, high], btype='band')
            filtered = filtfilt(b, a, signal)
            
            return filtered
        except Exception as e:
            if self.debug:
                print(f"[EVM] Filter error: {e}")
            return signal

    def _interpolate_signal(self, signal, timestamps, target_fs=30):
        """
        Resample signal to uniform sampling rate before FFT
        Handles dropped frames and timing jitter
        """
        try:
            if len(timestamps) < 2:
                return signal, target_fs
            
            # Create uniform time grid
            t_start = timestamps[0]
            t_end = timestamps[-1]
            duration = t_end - t_start
            
            if duration < 0.1:  # Less than 100ms
                return signal, target_fs
            
            # Create uniform time points
            num_samples = int(duration * target_fs) + 1
            t_uniform = np.linspace(t_start, t_end, num_samples)
            
            # Interpolate signal
            if len(signal) >= 2:
                f = interp1d(timestamps, signal, kind='linear', 
                            bounds_error=False, fill_value='extrapolate')
                signal_resampled = f(t_uniform)
                
                return signal_resampled, target_fs
            
            return signal, target_fs
            
        except Exception as e:
            if self.debug:
                print(f"[INTERPOLATE ERROR] {e}")
            return signal, target_fs

    def _detect_motion_artifacts(self, signal, fs):
        """
        Detect motion artifacts in signal
        Motion causes sudden spikes in the derivative
        Returns: (motion_detected, motion_ratio)
        """
        try:
            if len(signal) < 10:
                return False, 0.0
            
            # Calculate first derivative (velocity)
            derivative = np.diff(signal)
            derivative_magnitude = np.abs(derivative)
            
            # Threshold: mean + 3*std
            mean_deriv = np.mean(derivative_magnitude)
            std_deriv = np.std(derivative_magnitude)
            threshold = mean_deriv + 3 * std_deriv
            
            # Count motion frames
            motion_frames = np.sum(derivative_magnitude > threshold)
            motion_ratio = motion_frames / len(derivative)
            
            if self.debug and len(self.signal_buffer) % 120 == 0 and motion_ratio > 0.1:
                print(f"[MOTION] Detected {motion_ratio*100:.1f}% motion artifacts")
            
            # If >25% motion, signal is unreliable
            motion_detected = motion_ratio > 0.25
            
            return motion_detected, motion_ratio
            
        except Exception as e:
            if self.debug:
                print(f"[MOTION DETECTION ERROR] {e}")
            return False, 0.0

    def _calculate_bpm(self, signal, fs):
        """Calculate BPM from signal using FFT with detailed analysis"""
        if len(signal) < 60:  # Need at least 2 seconds of data at 30 FPS
            if self.debug:
                print(f"[BPM CALC] Not enough data: {len(signal)} samples")
            return None, 0.0
        
        try:
            # Apply FFT
            n = len(signal)
            window = np.hanning(len(signal))
            windowed_signal = signal * window
            fft_result = np.abs(fft(windowed_signal))
            frequencies = fftfreq(n, 1/fs)
            
            # Get positive frequencies only
            positive_mask = frequencies >= 0
            frequencies = frequencies[positive_mask]
            fft_result = fft_result[positive_mask]
            
            # Filter to heart rate range
            hr_mask = (frequencies >= self.freq_low) & (frequencies <= self.freq_high)
            if not np.any(hr_mask):
                if self.debug:
                    print(f"[BPM CALC] No frequencies in HR range")
                return None, 0.0
            
            hr_frequencies = frequencies[hr_mask]
            hr_fft = fft_result[hr_mask]
            
            # Find peak frequency
            peak_idx = np.argmax(hr_fft)
            peak_freq = hr_frequencies[peak_idx]
            peak_magnitude = hr_fft[peak_idx]
            
            # Calculate peak dominance (confidence metric)
            total_magnitude = np.sum(hr_fft)
            peak_dominance = peak_magnitude / total_magnitude if total_magnitude > 0 else 0
            # 🚨 Penalize frozen single-frequency dominance
            sorted_peaks = np.sort(hr_fft)
            if len(sorted_peaks) > 3:
               dominance_ratio = sorted_peaks[-1] / (sorted_peaks[-2] + 1e-6)
               if dominance_ratio > 8:
                 peak_dominance *= 0.6

            # Convert to BPM
            bpm = peak_freq * 60.0
            
            # Validate BPM
            if bpm < self.bpm_min or bpm > self.bpm_max:
                if self.debug:
                    print(f"[BPM CALC] BPM {bpm:.1f} outside range {self.bpm_min}-{self.bpm_max}")
                return None, 0.0
            
            if self.debug and len(self.signal_buffer) % 120 == 0:
                print(f"[BPM CALC] Peak: {peak_freq:.3f} Hz = {bpm:.1f} BPM (dominance: {peak_dominance:.3f})")
            
            return bpm, peak_dominance
            
        except Exception as e:
            if self.debug:
                print(f"[BPM CALC ERROR] {e}")
            return None, 0.0

    def _get_signal_quality(self, signal):
        """Calculate signal quality index (0.0 to 1.0)"""
        if len(signal) < 10:
            return 0.0
        
        try:
            # Metric 1: Signal range
            signal_range = np.max(signal) - np.min(signal)
            range_quality = min(signal_range / 2.0, 1.0)
            
            # Metric 2: Variance
            variance = np.var(signal)
            variance_quality = min(variance * 20, 1.0)
            
            # Metric 3: Signal stability (low derivative variance)
            derivative = np.diff(signal)
            deriv_std = np.std(derivative)
            stability_quality = 1.0 / (1.0 + deriv_std)
            
            # Combine metrics
            quality = (range_quality * 0.4 + variance_quality * 0.4 + stability_quality * 0.2)
            
            return min(quality, 1.0)
            
        except Exception as e:
            if self.debug:
                print(f"[QUALITY ERROR] {e}")
            return 0.0

    def _calculate_confidence(self, quality, peak_dominance, motion_ratio):
        """
        Multi-factor confidence assessment
        Combines signal quality, FFT peak dominance, and motion
        """
        score = 0.0
        
        # Factor 1: Signal quality (40%)
        if quality > 0.6:
            score += 0.40
        elif quality > 0.3:
            score += 0.25
        else:
            score += 0.05
        
        # Factor 2: FFT peak dominance (40%)
        if peak_dominance > 0.10:
            score += 0.40
        elif peak_dominance > 0.05:
            score += 0.25
        else:
            score += 0.05
        
        # Factor 3: Motion artifacts (20%)
        if motion_ratio < 0.1:
            score += 0.20
        elif motion_ratio < 0.2:
            score += 0.10
        
        # Convert to categorical
        if score > 0.55:
            return "HIGH"
        elif score > 0.35:
            return "MEDIUM"
        else:
            return "LOW"

    def _validate_signal(self, signal, fs):
        """Validate if signal contains heart rate patterns"""
        if len(signal) < 30:
            return False, "Signal too short"
        
        try:
            # Check 1: Minimum amplitude
            signal_range = np.max(signal) - np.min(signal)
            if signal_range < 0.5:
                return False, f"Signal too flat (range: {signal_range:.3f})"
            
            # Check 2: Check for dominant frequency using FFT
            fft_vals = np.abs(fft(signal))
            freqs = fftfreq(len(signal), 1/fs)
            
            # Focus on HR range
            hr_mask = (freqs >= self.freq_low) & (freqs <= self.freq_high)
            if not np.any(hr_mask):
                return False, "No frequencies in HR range"
            
            hr_fft = fft_vals[hr_mask]
            
            # Check if peak is significant
            peak_mag = np.max(hr_fft)
            total_mag = np.sum(fft_vals)
            peak_ratio = peak_mag / total_mag if total_mag > 0 else 0
            
            if peak_ratio < 0.015:  # Peak not dominant enough
                return False, f"Weak peak (ratio: {peak_ratio:.3f})"
            
            return True, "Valid signal"
            
        except Exception as e:
            if self.debug:
                print(f"[VALIDATE ERROR] {e}")
            return False, str(e)

    def update(self, roi):
        """
        Process ROI and return BPM estimate
        roi: forehead region (BGR image)
        Returns: (bpm, confidence)
        """
        current_time = time.time()
        
        # Check if ROI is valid
        if roi is None or roi.size == 0:
            self.confidence = "LOW"
            return self.smoothed_bpm, self.confidence
        
        roi_height, roi_width = roi.shape[:2]
        if roi_height < 10 or roi_width < 10:
            if self.debug:
                print(f"[ROI] Too small: {roi_width}x{roi_height}")
            self.confidence = "LOW"
            return self.smoothed_bpm, self.confidence
        
        try:
            # Adjust brightness if needed
            roi_adjusted = self._adjust_brightness(roi)
            
            # Extract green channel signal
            signal_value = self._extract_green_signal(roi_adjusted)
            
            if signal_value is None:
                self.confidence = "LOW"
                return self.smoothed_bpm, self.confidence
            
            # Add to buffer
            self.signal_buffer.append(signal_value)
            self.time_buffer.append(current_time)
            
            # Store for debugging/plotting
            self.signal_history.append(signal_value)
            if len(self.signal_history) > 300:  # Keep last 10 seconds at 30fps
                self.signal_history.pop(0)
                
        except Exception as e:
            if self.debug:
                print(f"[EVM] ROI processing error: {e}")
            self.confidence = "LOW"
            return self.smoothed_bpm, self.confidence
        
        # 🚨 CHANGED: lowered minimum buffer size from 4 seconds to 2 seconds for faster testing
        min_samples_needed = int(self.fs * 1)  
        
        if len(self.signal_buffer) < min_samples_needed:
            self.confidence = "LOW"
            if self.debug:
                print(f"[BUFFERING] {len(self.signal_buffer)}/{min_samples_needed} frames collected...")
            return None, self.confidence
        
        # Calculate BPM at intervals
        time_since_last = current_time - self.last_update_time
        
        if time_since_last >= self.update_interval:
            self.last_update_time = current_time
            
            if self.debug:
                print(f"\n[EVM UPDATE] Buffer: {len(self.signal_buffer)} samples, "
                      f"Time interval: {time_since_last:.1f}s")
            
            # Convert buffers to arrays
            signal = np.array(self.signal_buffer)
            timestamps = np.array(self.time_buffer)
            
            # Interpolate to uniform sampling rate
            signal_uniform, actual_fs = self._interpolate_signal(signal, timestamps, target_fs=self.fs)
            
            # Remove DC component
            signal_detrended = signal_uniform - np.mean(signal_uniform)
            
            # Apply bandpass filter
            filtered = self._bandpass_filter(signal_detrended, actual_fs)
            
            # Detect motion artifacts
            motion_detected, motion_ratio = self._detect_motion_artifacts(filtered, actual_fs)
            
            # Validate signal
            is_valid, validation_msg = self._validate_signal(filtered, actual_fs)
            
            if not is_valid:
                self.confidence = "LOW"
                self.consecutive_failures += 1
                
                if self.debug:
                    print(f"[VALIDATION FAILED] {validation_msg}")
                
                # If too many failures, clear buffer
                if self.consecutive_failures > 5:
                    if self.debug:
                        print("[VALIDATION] Too many failures, clearing buffer")
                    self.signal_buffer.clear()
                    self.time_buffer.clear()
                    self.consecutive_failures = 0
                
                return self.smoothed_bpm, self.confidence
            
            # Reset failure counter
            self.consecutive_failures = 0
            

            # Calculate BPM and peak dominance
            bpm, peak_dominance = self._calculate_bpm(filtered, actual_fs)
            
            # Calculate signal quality
            quality = self._get_signal_quality(filtered)
            
            # Calculate confidence
            confidence = self._calculate_confidence(quality, peak_dominance, motion_ratio)
            self.last_peak_dominance = peak_dominance
            self.last_signal_quality = quality
            self.last_motion_ratio = motion_ratio
            if self.smoothed_bpm is not None:
              if abs(bpm - self.smoothed_bpm) > 25:
                self.confidence = "LOW"
                return self.smoothed_bpm, self.confidence
            if bpm is not None:
                # Add to history
                self.bpm_history.append(bpm)
                
                # Validate against previous BPM (sanity check)
                if self.current_bpm is not None and len(self.bpm_history) > 3:
                    recent_bpms = list(self.bpm_history)[-5:] if len(self.bpm_history) >= 5 else list(self.bpm_history)
                    moving_avg = np.mean(recent_bpms)
                    moving_std = np.std(recent_bpms)
                    
                    # Check if new BPM is within 2 standard deviations
                    if moving_std > 0.5 and abs(bpm - moving_avg) > 2 * moving_std:
                        if self.debug:
                            print(f"[SANITY CHECK] BPM {bpm:.1f} outside normal "
                                  f"(avg: {moving_avg:.1f}, std: {moving_std:.1f}), using moving avg")
                        bpm = moving_avg
                
                # First valid reading
                if self.current_bpm is None:
                    self.current_bpm = bpm
                    self.smoothed_bpm = bpm
                    self.last_valid_bpm_time = current_time
                    self.confidence = confidence
                    
                    if self.debug:
                        print(f"[FIRST READING] BPM: {bpm:.1f}, Quality: {quality:.3f}, "
                              f"Dominance: {peak_dominance:.3f}, Confidence: {confidence}")
                else:
                    # Smooth BPM value
                    alpha = 0.4 if quality > 0.5 else 0.2
                    self.smoothed_bpm = alpha * bpm + (1 - alpha) * self.smoothed_bpm
                    self.current_bpm = bpm
                    self.last_valid_bpm_time = current_time
                    self.confidence = confidence
                    
                    if self.debug:
                        print(f"[RESULT] Raw: {bpm:.1f}, Smoothed: {self.smoothed_bpm:.1f}, "
                              f"Quality: {quality:.3f}, Conf: {confidence}")
            
            else:
                self.confidence = "LOW"
                if self.debug:
                    print(f"[NO BPM] Quality: {quality:.3f}, Motion: {motion_ratio:.3f}")
        
        # If no BPM for too long, reset confidence
        if (self.current_bpm is not None and 
            current_time - self.last_valid_bpm_time > 10.0):
            self.confidence = "LOW"
            if self.debug:
                print(f"[TIMEOUT] No valid BPM for 10s, confidence reset to LOW")
        
        return self.smoothed_bpm, self.confidence
    
    def get_debug_info(self):
       """Return debug information"""
       return {
        'buffer_size': len(self.signal_buffer),
        'current_bpm': self.current_bpm,
        'smoothed_bpm': self.smoothed_bpm,
        'confidence': self.confidence,
        'signal_history_length': len(self.signal_history),
        'bpm_history_length': len(self.bpm_history),
        'freq_low': self.freq_low,
        'freq_high': self.freq_high,
        'consecutive_failures': self.consecutive_failures,
        'peak_dominance': getattr(self, 'last_peak_dominance', 0.0),
        'signal_quality': getattr(self, 'last_signal_quality', 0.0),
        'motion_ratio': getattr(self, 'last_motion_ratio', 0.0),
      }

    
    def plot_signal_ascii(self, num_samples=50):
        """Create ASCII plot of recent signal"""
        if len(self.signal_history) < 10:
            return "Not enough data"
        
        signal = self.signal_history[-num_samples:]
        min_val = min(signal)
        max_val = max(signal)
        range_val = max_val - min_val
        
        if range_val == 0:
            return "Signal flat"
        
        # Scale to 10 rows
        height = 10
        scaled = [int((s - min_val) / range_val * height) for s in signal]
        
        plot_str = "\nSignal (last {} samples):\n".format(num_samples)
        for y in range(height, -1, -1):
            line = "▏"
            for val in scaled:
                if val >= y:
                    line += "█"
                else:
                    line += " "
            line += "▕"
            plot_str += line + "\n"
        
        plot_str += f"Min: {min_val:.1f}, Max: {max_val:.1f}, Range: {range_val:.3f}"
        
        # Add trend indicator
        if len(signal) > 10:
            first_half = np.mean(signal[:len(signal)//2])
            second_half = np.mean(signal[len(signal)//2:])
            if second_half > first_half + 0.5:
                plot_str += " ↗"
            elif second_half < first_half - 0.5:
                plot_str += " ↘"
            else:
                plot_str += " →"
        
        return plot_str
    
    def reset(self):
        """Reset the EVM processor"""
        self.signal_buffer.clear()
        self.time_buffer.clear()
        self.signal_history.clear()
        self.bpm_history.clear()
        self.current_bpm = None
        self.smoothed_bpm = None
        self.confidence = "LOW"
        self.consecutive_failures = 0
        self.last_valid_bpm_time = 0
        
        if self.debug:
            print("[EVM] Processor reset")