import torch
import nemo.collections.asr as nemo_asr
import numpy as np
import logging

logger = logging.getLogger(__name__)

class NeMoIntentModel:
    def __init__(self, model_name="slu_conformer_transformer_large_slurp", device="auto"):
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if (device == "auto" and torch.cuda.is_available()) else "cpu"
        logger.info(f"Using device: {self.device}")
        self._load_model()
    
    def _load_model(self):
        try:
            logger.info(f"Loading NeMo model: {self.model_name}")
            self.model = nemo_asr.models.SLUIntentSlotBPEModel.from_pretrained(
                model_name=self.model_name
            )
            self.model = self.model.to(self.device)
            self.model.eval()
            logger.info("✓ Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def infer(self, audio):
        """Run inference on audio"""
        if self.model is None:
            logger.error("Model not loaded")
            return None
        
        try:
            with torch.no_grad():
                predictions = self.model.transcribe(audio=[audio], batch_size=1)
            
            if predictions and len(predictions) > 0:
                return predictions
        except Exception as e:
            logger.error(f"Inference error: {e}")
        
        return None
    
    def parse_intent_output(self, intent_string):
        """Parse intent output into structured format"""
        if not intent_string:
            return {"intent": "unknown", "slots": {}}
        
        parts = intent_string.strip().split()
        if not parts:
            return {"intent": "unknown", "slots": {}}
        
        intent = parts
        slots = {}
        for part in parts[1:]:
            if ":" in part:
                slot_name, slot_value = part.split(":", 1)
                slots[slot_name] = slot_value
        
        return {"intent": intent, "slots": slots}
