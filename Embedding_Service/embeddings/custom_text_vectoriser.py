"""Custom text vectorizer using a transformer model for generating embeddings."""
from typing import List, Dict
import numpy as np

class EmbeddingGenerator:

    """Callable class for generating embeddings using map_batches."""

    def __init__(
        self,
        model_name: str,
        micro_batch_size: int,
    ):
        import torch
        from transformers import AutoModel, AutoTokenizer
        
        self.torch = torch
        self.model_name = model_name
        self.micro_batch_size = micro_batch_size

        if self.torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
        self.model.eval()


    def last_token_pool(self, last_hidden_states, attention_mask):
        """Apply last token pooling to get sentence embeddings."""
        left_padding = attention_mask[:, -1].sum() == attention_mask.shape[0]
        if left_padding:
            return last_hidden_states[:, -1]
        else:
            sequence_lengths = attention_mask.sum(dim=1) - 1
            batch_size = last_hidden_states.shape[0]
            return last_hidden_states[
                self.torch.arange(batch_size, device=last_hidden_states.device), 
                sequence_lengths
            ]

    def __call__(self, batch: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Generate embeddings for a batch."""
        try:
            if isinstance(batch["text"], np.ndarray):
                texts = batch["text"].tolist()
            else:
                texts = list(batch["text"])


            all_embeddings = []

            # Process in micro-batches
            for i in range(0, len(texts), self.micro_batch_size):
                batch_texts = texts[i:i + self.micro_batch_size]

                encoded_input = self.tokenizer(
                    batch_texts, 
                    padding=True, 
                    truncation=True, 
                    max_length=512, 
                    return_tensors="pt"
                ).to(self.device)

                with self.torch.no_grad():
                    model_output = self.model(**encoded_input)
                    embeddings = self.last_token_pool(
                        model_output.last_hidden_state, 
                        encoded_input["attention_mask"]
                    )
                    all_embeddings.append(embeddings.cpu().numpy())

            batch["embedding"] = np.concatenate(all_embeddings, axis=0)
            return batch

        except Exception as e:
            raise

 