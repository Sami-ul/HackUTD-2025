import base64
import audioop
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TwilioAudioProcessor:
    def __init__(self, twilio_sample_rate=8000, target_sample_rate=16000):
        self.twilio_sample_rate = twilio_sample_rate
        self.target_sample_rate = target_sample_rate
        self.audio_buffer = []
    
    def process_twilio_audio_chunk(self, base64_payload):
        """8kHz μ-law → 16kHz PCM"""
        try:
            # Decode base64
            mulaw_bytes = base64.b64decode(base64_payload)
            
            # Convert μ-law to PCM
            pcm_bytes = audioop.ulaw2lin(mulaw_bytes, 2)
            
            # Resample 8kHz → 16kHz
            resampled, _ = audioop.ratecv(
                pcm_bytes, 2, 1, self.twilio_sample_rate, 
                self.target_sample_rate, None
            )
            
            return resampled
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return b""
    
    def bytes_to_numpy(self, audio_bytes):
        """Convert bytes to float32 numpy array"""
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0
        return audio_float
    
    def accumulate_audio(self, audio_bytes):
        self.audio_buffer.append(audio_bytes)
    
    def get_accumulated_audio(self):
        if not self.audio_buffer:
            return np.array([], dtype=np.float32)
        combined_bytes = b"".join(self.audio_buffer)
        audio_array = self.bytes_to_numpy(combined_bytes)
        self.audio_buffer = []
        return audio_array
    
    def clear_buffer(self):
        self.audio_buffer = []
