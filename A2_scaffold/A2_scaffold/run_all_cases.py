#!/usr/bin/env python3
"""
Run ALL 55 test cases (15 original + 40 generated)

This script:
1. Sets the data path automatically
2. Switches to LIVE backend temporarily
3. Runs all cases with --all flag
4. Generates both JSON and TXT reports
5. Shows summary of results

REQUIREMENTS:
- OpenRouter API key set in environment
- Or will prompt you to enter it

COST: ~$0.15-0.25 (gpt-4o-mini)
TIME: 5-10 minutes
"""
import os
import sys
import subprocess

# Set data path
os.environ['A2_DATA'] = r'd:\Github\PE6201_A2\A2_reference_data\A2_reference_data'

def main():
    print("="*70)
    print("Running ALL 55 Test Cases")
    print("="*70)
    print()

    # Check for API key
    api_key = os.environ.get('OPENROUTER_API_KEY', '')

    if not api_key:
        print("⚠ No OPENROUTER_API_KEY found in environment!")
        print()
        print("You have two options:")
        print()
        print("1. Set the environment variable:")
        print("   Windows (PowerShell): $env:OPENROUTER_API_KEY='sk-or-v1-...'")
        print("   Windows (CMD):        set OPENROUTER_API_KEY=sk-or-v1-...")
        print("   Linux/Mac:            export OPENROUTER_API_KEY='sk-or-v1-...'")
        print()
        print("2. Enter it now (will be used for this run only):")
        try:
            api_key = input("API Key: ").strip()
            if api_key:
                os.environ['OPENROUTER_API_KEY'] = api_key
            else:
                print("\n❌ No API key provided. Exiting.")
                return 1
        except (KeyboardInterrupt, EOFError):
            print("\n\n❌ Cancelled.")
            return 1

    print("✓ API key found")
    print()

    # Check backend setting
    import config
    current_backend = config.BACKEND

    if current_backend != "live":
        print(f"⚠ Current backend is '{current_backend}', but we need 'live'")
        print()
        print("To run all cases, you need to temporarily use the LIVE backend.")
        print("This will:")
        print("  - Use the actual OpenAI model")
        print("  - Cost approximately $0.15-0.25")
        print("  - Take 5-10 minutes")
        print()
        response = input("Continue and switch to live backend? [y/N]: ").strip().lower()

        if response != 'y':
            print("\n❌ Cancelled.")
            print("\nAlternatively, you can:")
            print("1. Edit config.py and set: BACKEND = 'live'")
            print("2. Run: python run_eval_with_report.py --all")
            return 1

        print("\n⚠ Note: This script will NOT modify config.py")
        print("You need to manually edit config.py and set:")
        print("   BACKEND = 'live'")
        print()
        response = input("Have you changed config.py to BACKEND='live'? [y/N]: ").strip().lower()

        if response != 'y':
            print("\n❌ Please edit config.py first, then run this script again.")
            return 1

    # Run the evaluation
    print()
    print("="*70)
    print("Starting evaluation of all 55 cases...")
    print("="*70)
    print()

    try:
        # Import and run
        import run_eval

        # Run with --all flag
        result = run_eval.main(['run_all_cases.py', '--all'])

        print()
        print("="*70)
        print("✓ Evaluation Complete!")
        print("="*70)
        print()
        print("Generated files:")
        print("  ✓ results.json - Machine-readable JSON")
        print("  ✓ evaluation_report.txt - Human-readable report")
        print()
        print("Next steps:")
        print("  1. Review evaluation_report.txt for detailed results")
        print("  2. Check results.json for programmatic analysis")
        print("  3. Commit both files to your repository")
        print()

        return result

    except Exception as e:
        print()
        print("="*70)
        print("❌ Error running evaluation:")
        print(str(e))
        print("="*70)
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
