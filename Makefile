.PHONY: film validate keyframes narration clean

validate:
	python -m pipeline.validate storyboard.json schema/storyboard.schema.json

film: validate
	python -m pipeline.run storyboard.json

keyframes:
	python -m pipeline.run_stage keyframes

narration:
	python -m pipeline.run_stage narration

clean:
	rm -rf outputs/final_* outputs/temp_*