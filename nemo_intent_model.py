import torch
import nemo.collections.asr as nemo_asr
import numpy as np
import logging

logger = logging.getLogger(__name__)

class NeMoIntentModel:
    def __init__(self, model_name="stt_en_quartznet15x5", device="auto"):
        """
        NeMo ASR Model for speech-to-text transcription
        Using QuartzNet for fast, accurate English speech recognition
        """
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if (device == "auto" and torch.cuda.is_available()) else "cpu"
        logger.info(f"Using device: {self.device}")
        self._load_model()
    
    def _load_model(self):
        try:
            logger.info(f"Loading NeMo ASR model: {self.model_name}")
            # Use standard ASR model for speech-to-text
            self.model = nemo_asr.models.EncDecCTCModel.from_pretrained(
                model_name=self.model_name
            )
            self.model = self.model.to(self.device)
            self.model.eval()
            logger.info("✓ ASR Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def infer(self, audio):
        """Run inference on audio to get transcription"""
        if self.model is None:
            logger.error("Model not loaded")
            return None
        
        try:
            # Convert numpy array to torch tensor if needed
            if isinstance(audio, np.ndarray):
                audio_tensor = torch.from_numpy(audio).float()
            else:
                audio_tensor = audio
            
            # Ensure audio is on the correct device
            audio_tensor = audio_tensor.to(self.device)
            
            # Add batch dimension if needed
            if audio_tensor.dim() == 1:
                audio_tensor = audio_tensor.unsqueeze(0)
            
            # Get audio length
            audio_length = torch.tensor([audio_tensor.shape[1]]).to(self.device)
            
            # Transcribe using forward pass
            with torch.no_grad():
                log_probs, encoded_len, greedy_predictions = self.model(
                    input_signal=audio_tensor,
                    input_signal_length=audio_length
                )
                
                # Decode using the model's decoder
                # Use the vocabulary to decode predictions
                hypotheses = []
                for batch_ind in range(greedy_predictions.shape[0]):
                    prediction = greedy_predictions[batch_ind].cpu().numpy()
                    # Convert indices to characters using model's vocabulary
                    decoded = ""
                    for idx in prediction:
                        idx_int = int(idx)  # Convert numpy int64 to Python int
                        if idx_int < len(self.model.decoder.vocabulary):
                            decoded += self.model.decoder.vocabulary[idx_int]
                    hypotheses.append(decoded.strip())
                
                transcription = hypotheses[0] if hypotheses else ""
                logger.info(f"Transcription: {transcription}")
                return transcription
                
        except Exception as e:
            logger.error(f"Inference error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return None
    
    def parse_intent_output(self, transcription):
        """
        Parse transcription into basic intent structure
        The actual intent extraction will be done by the Nemotron agent
        """
        if not transcription:
            return {"transcription": "", "intent": "unknown", "slots": {}}
        
        transcription_lower = transcription.lower().strip()
        
        # Simple keyword-based intent detection (fallback)
        intent = "general_inquiry"
        
        if any(word in transcription_lower for word in ["bill", "balance", "owe", "due", "payment amount"]):
            intent = "check_bill"
        elif any(word in transcription_lower for word in ["pay", "payment", "paying"]):
            intent = "make_payment"
        elif any(word in transcription_lower for word in ["cancel", "disconnect", "stop service"]):
            intent = "cancel_service"
        elif any(word in transcription_lower for word in ["help", "support", "problem", "issue", "not working"]):
            intent = "technical_support"
        elif any(word in transcription_lower for word in ["speak", "human", "agent", "representative"]):
            intent = "speak_to_human"
        
        return {
            "transcription": transcription,
            "intent": intent,
            "slots": {}
        }
