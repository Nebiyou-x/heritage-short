.PHONY: film mock-film validate keyframes narration clean

validate:
	python -m pipeline.validate storyboard.json schema/storyboard.schema.json

film: validate
	USE_MOCK=0 KEYFRAMES_PROVIDER=cloudflare NARRATION_PROVIDER=gemini python -m pipeline.run storyboard.json

mock-film: validate
	USE_MOCK=1 python -m pipeline.run storyboard.json

keyframes:
	python -m pipeline.run_stage keyframes

narration:
	python -m pipeline.run_stage narration

clean:
	rm -rf outputs/final_* outputs/temp_*