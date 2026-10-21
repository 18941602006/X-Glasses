"""Explicit, local-only LocateAnything inference for the PC evaluation prototype."""

from __future__ import annotations

import re
import time
from pathlib import Path

MODEL_REPO = "nvidia/LocateAnything-3B"
MODEL_REVISION = "c32291ca5e996f5a7a485845b4f57a233936bba0"
MODEL_ID = f"{MODEL_REPO}@{MODEL_REVISION}"
DEFAULT_MODEL = Path("models/LocateAnything-3B")
BOX_PATTERN = re.compile(r"<box><(\d+)><(\d+)><(\d+)><(\d+)></box>")


def parse_model_boxes(answer: str) -> list[list[float]]:
    """Decode the documented 0..1000 coordinate tokens; never invent confidence."""
    if not isinstance(answer, str) or len(answer) > 32_768:
        raise ValueError("invalid model response")
    matches = BOX_PATTERN.findall(answer)
    if len(matches) > 16:
        raise ValueError("too many detections; narrow the query")
    boxes = []
    for match in matches:
        x1, y1, x2, y2 = map(int, match)
        if not (0 <= x1 < x2 <= 1000 and 0 <= y1 < y2 <= 1000):
            raise ValueError("invalid model coordinates")
        boxes.append([x1 / 1000, y1 / 1000, x2 / 1000, y2 / 1000])
    if not matches and "<box>none</box>" not in answer:
        raise ValueError("model returned no valid box or explicit none")
    return boxes


class PcLocateRuntime:
    """Run in its own process/environment, outside the live risk-monitoring loop."""

    def __init__(self, model_dir: Path = DEFAULT_MODEL):
        import torch
        from transformers import AutoConfig, AutoModel, AutoProcessor, AutoTokenizer

        marker = model_dir / "xg_revision.txt"
        if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != MODEL_REVISION:
            raise ValueError("prepare the pinned model using python -m tools.prepare_locate_pc")
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable; use the isolated CUDA PyTorch environment")
        self.torch = torch
        self.device = "cuda"
        self.dtype = torch.bfloat16
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        self.processor = AutoProcessor.from_pretrained(
            model_dir, trust_remote_code=True, local_files_only=True
        )
        config = AutoConfig.from_pretrained(
            model_dir, trust_remote_code=True, local_files_only=True
        )
        config._attn_implementation = "sdpa"
        config.text_config._attn_implementation = "sdpa"
        config.vision_config._attn_implementation = "sdpa"
        self.model = (
            AutoModel.from_pretrained(
                model_dir,
                config=config,
                torch_dtype=self.dtype,
                trust_remote_code=True,
                local_files_only=True,
                low_cpu_mem_usage=True,
            )
            .to(self.device)
            .eval()
        )

    def locate(self, image, query: str, *, source: str) -> dict:
        query = query.strip()
        if not query or len(query) > 160 or any(not c.isprintable() for c in query):
            raise ValueError("query must contain 1..160 printable characters")
        if source not in {"file", "pc_camera"}:
            raise ValueError("explicit PC image source required")
        image = image.convert("RGB")
        if image.width * image.height > 16_000_000:
            raise ValueError("image exceeds 16 megapixels")
        image.thumbnail((640, 480))
        prompt = f"Locate all the instances that match the following description: {query}."
        messages = [
            {
                "role": "user",
                "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}],
            }
        ]
        text = self.processor.py_apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        images, videos = self.processor.process_vision_info(messages)
        inputs = self.processor(text=[text], images=images, videos=videos, return_tensors="pt").to(
            self.device
        )
        torch = self.torch
        torch.cuda.synchronize()
        started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats()
        with torch.inference_mode():
            response = self.model.generate(
                pixel_values=inputs["pixel_values"].to(self.dtype),
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                image_grid_hws=inputs.get("image_grid_hws"),
                tokenizer=self.tokenizer,
                max_new_tokens=256,
                use_cache=True,
                generation_mode="slow",
                do_sample=False,
                verbose=False,
            )
        torch.cuda.synchronize()
        answer = response[0] if isinstance(response, tuple) else response
        boxes = parse_model_boxes(answer)
        return {
            "model_id": MODEL_ID,
            "source": source,
            "query": query,
            "image_size": list(image.size),
            "answer": answer,
            "boxes": boxes,
            "confidence": None,
            "distance_m": None,
            "tof_status": "not_connected",
            "grasp_confirmed": False,
            "inference_ms": round((time.perf_counter() - started) * 1000, 2),
            "peak_cuda_allocated_mib": round(torch.cuda.max_memory_allocated() / 2**20, 1),
        }
