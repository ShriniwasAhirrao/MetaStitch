from src.agents.text_extractor.text_extractor_agent import TextExtractorAgent
from src.pipelines.pipeline_orchestrator import PipelineOrchestrator

def main():
    print("Starting the universal main workflow...")

    # Initialize core components
    text_extractor_agent = TextExtractorAgent()
    pipeline_orchestrator = PipelineOrchestrator()

    # Placeholder for running the main workflow
    # Since pipeline_orchestrator code is empty, just print a message
    print("Running pipeline orchestrator...")
    # pipeline_orchestrator.run()  # Uncomment when implemented

    print("Workflow completed successfully.")

if __name__ == "__main__":
    main()
