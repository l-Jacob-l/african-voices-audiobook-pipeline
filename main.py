from pipeline import run_pipeline

if __name__ == "__main__":
    text = """
    Dr. Smith published findings in 2024 showing that 87% of participants
    experienced improvements. The study, which lasted 18 months, involved
    3 distinct phases: screening, treatment, and follow-up evaluation.
    Key outcomes included reduced symptoms, improved quality of life, and
    lower hospitalization rates (down 42% vs. control group).
    """

    result = run_pipeline(text, output_name="narration")
    print(f"\nDone. Audio at: {result.audio_path}")
