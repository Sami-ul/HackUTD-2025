"""
ElevenLabs Text-to-Speech Handler for Twilio Media Streams
Converts text to mulaw audio format for real-time streaming
"""

import os
import io
import base64
import audioop
import logging
from elevenlabs import ElevenLabs, VoiceSettings

logger = logging.getLogger(__name__)


class ElevenLabsTTSHandler:
    def __init__(self):
        """
        Initialize ElevenLabs TTS client
        Requires ELEVENLABS_API_KEY environment variable
        """
        api_key = os.getenv("ELEVENLABS_API_KEY")
        
        if not api_key:
            logger.warning("ELEVENLABS_API_KEY not set - TTS will not work!")
            logger.warning("Get your API key from: https://elevenlabs.io/app/settings/api-keys")
            self.client = None
            return
        
        try:
            self.client = ElevenLabs(api_key=api_key)
            
            # Default voice settings
            self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - natural, friendly
            # Other popular voices:
            # "EXAVITQu4vr4xnSDxMaL" - Bella - soft, kind
            # "ErXwobaYiN019PkySvjV" - Antoni - well-rounded male
            # "MF3mGyEYCl7XYWbV9V6O" - Elli - expressive female
            
            self.voice_settings = VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
            
            logger.info("✓ ElevenLabs TTS Handler initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabs TTS: {e}")
            self.client = None
    
    def text_to_mulaw_base64(self, text):
        """
        Convert text to mulaw audio encoded in base64 for Twilio
        
        Args:
            text: The text to convert to speech
            
        Returns:
            base64 encoded mulaw audio string
        """
        if not self.client:
            logger.error("ElevenLabs TTS client not initialized")
            return None
        
        try:
            # Step 1: Generate speech with ElevenLabs
            # Using stream to get audio data
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_turbo_v2_5",  # Fast, low-latency model
                voice_settings=self.voice_settings,
                output_format="pcm_16000"  # 16kHz PCM
            )
            
            # Collect audio chunks
            audio_chunks = []
            for chunk in audio_generator:
                if chunk:
                    audio_chunks.append(chunk)
            
            # Combine all chunks
            pcm_audio = b''.join(audio_chunks)
            
            if not pcm_audio:
                logger.error("No audio data received from ElevenLabs")
                return None
            
            # Step 2: Downsample from 16kHz to 8kHz (Twilio requirement)
            resampled_audio, _ = audioop.ratecv(
                pcm_audio,
                2,      # 2 bytes per sample (16-bit)
                1,      # mono
                16000,  # input rate
                8000,   # output rate (Twilio)
                None
            )
            
            # Step 3: Convert PCM to mulaw (Twilio format)
            mulaw_audio = audioop.lin2ulaw(resampled_audio, 2)
            
            # Step 4: Encode to base64
            base64_audio = base64.b64encode(mulaw_audio).decode('utf-8')
            
            logger.info(f"Generated ElevenLabs TTS: {len(text)} chars → {len(base64_audio)} bytes")
            
            return base64_audio
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS conversion error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def text_to_twilio_chunks(self, text, chunk_size=160):
        """
        Convert text to speech and split into chunks for streaming
        
        Args:
            text: Text to convert
            chunk_size: Size of each chunk in bytes (160 bytes = 20ms at 8kHz mulaw)
            
        Returns:
            List of base64 encoded audio chunks
        """
        base64_audio = self.text_to_mulaw_base64(text)
        
        if not base64_audio:
            return []
        
        # Decode from base64 to get raw mulaw bytes
        mulaw_bytes = base64.b64decode(base64_audio)
        
        # Split into chunks
        chunks = []
        for i in range(0, len(mulaw_bytes), chunk_size):
            chunk = mulaw_bytes[i:i + chunk_size]
            # Encode each chunk to base64
            chunks.append(base64.b64encode(chunk).decode('utf-8'))
        
        logger.info(f"Split audio into {len(chunks)} chunks for streaming")
        
        return chunks
    
    def set_voice(self, voice_id):
        """
        Change the voice used for TTS
        
        Popular voices:
        - "21m00Tcm4TlvDq8ikWAM" - Rachel (default)
        - "EXAVITQu4vr4xnSDxMaL" - Bella
        - "ErXwobaYiN019PkySvjV" - Antoni
        - "MF3mGyEYCl7XYWbV9V6O" - Elli
        
        See all voices: https://elevenlabs.io/app/voice-library
        """
        self.voice_id = voice_id
        logger.info(f"Voice changed to: {voice_id}")


# Global instance
tts_handler = ElevenLabsTTSHandler()
