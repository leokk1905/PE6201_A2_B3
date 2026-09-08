"""
Run all cells from A2_Scaffold_Tour_ProblemB.ipynb sequentially
Output is saved to notebook_output.txt
"""
import os
import sys
import json
from datetime import datetime

# Set the data path
os.environ['A2_DATA'] = r'd:\Github\PE6201_A2\A2_reference_data\A2_reference_data'

# Add current directory to path
sys.path.insert(0, '.')

# Open output file
output_file = 'notebook_output.txt'
original_stdout = sys.stdout

class TeeOutput:
    """Write to both console and file simultaneously"""
    def __init__(self, file_handle):
        self.terminal = original_stdout
        self.log = file_handle

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

# Start capturing output
log_file = open(output_file, 'w', encoding='utf-8')
sys.stdout = TeeOutput(log_file)

print(f"A2_Scaffold_Tour_ProblemB Output")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
print()

# Cell 1: Setup
print("="*70)
print("CELL 1: SETUP")
print("="*70)
import config
print(config.summary())
print('data:', config.data_root())
print()

# Cell 2: What the agent is handed
print("="*70)
print("CELL 2: WHAT THE AGENT IS HANDED")
print("="*70)
import tools

referral = tools.get_referral('REF-5602')
print(json.dumps(referral, indent=1))
print()
print('specialty on this referral :', referral['specialty'])
print('patient on this referral   :', referral['patient_id'])
print()

# Cell 3: The rules
print("="*70)
print("CELL 3: THE RULES THE AGENT MUST REACH")
print("="*70)
print('the clock (as_of):', tools.as_of())
print()
criteria = tools.check_referral_criteria('OPH', 'REF-5602')
print(json.dumps(criteria, indent=1))
print()
print('-> band %r means %s %d-week window measured from as_of'
      % (criteria['band'],
         'an' if criteria['window_weeks'] == 8 else 'a',
         criteria['window_weeks']))
print()

# Cell 4: The trap
print("="*70)
print("CELL 4: THE TRAP IN THIS CASE")
print("="*70)
WINDOW_OPEN, WINDOW_CLOSE = '2026-09-09', '2026-11-04'

for s in tools._load('B', 'clinic_slots'):
    if s['specialty'] != 'OPH':
        continue
    inside = WINDOW_OPEN <= s['date'] <= WINDOW_CLOSE
    free   = s['capacity_remaining'] > 0
    if inside and free and s['band'] != 'routine':
        note = '   <-- in window, free, but WRONG BAND'
    elif inside and free:
        note = '   <-- legal and bookable'
    elif inside and not free:
        note = '   (in window but FULL - exists, cannot be booked)'
    else:
        note = ''
    print('%-8s %-8s %s %s  cap=%d%s'
          % (s['clinic'], s['band'], s['date'], s['time'],
             s['capacity_remaining'], note))
print()

# Cell 5: The run itself
print("="*70)
print("CELL 5: THE RUN ITSELF")
print("="*70)
from agent import run_case

record = run_case('REF-5602', verbose=True)
print()

# Cell 6: The decision record
print("="*70)
print("CELL 6: THE DECISION RECORD")
print("="*70)
print(json.dumps(record, indent=2))
print()

# Cell 7: Grading - code check
print("="*70)
print("CELL 7: GRADING - CODE CHECK")
print("="*70)
from harness import load_key, code_check, prepare_judgement_check

expected = load_key('B')['REF-5602']
print('THE ANSWER KEY SAYS:')
print(json.dumps(expected, indent=1))

passed, fails = code_check(record, expected)
print()
print('CODE CHECK:', 'PASS' if passed else 'FAIL')
for f in fails:
    print('   ', f)
print()

# Cell 8: Grading - judgement check
print("="*70)
print("CELL 8: GRADING - JUDGEMENT CHECK")
print("="*70)
item = prepare_judgement_check(record, expected)

print('The reason the agent gave:')
print('   ', item['reason'])
print()
print('Does it carry each of these? Nobody has ruled yet:')
for m in item['must_record']:
    print('  [ ]', m)
print()
print('verdict:', item['verdict'], '   graded_by:', item['graded_by'])
print()

# Cell 9: The failure that raises no exception
print("="*70)
print("CELL 9: THE FAILURE THAT RAISES NO EXCEPTION (D7)")
print("="*70)
import demo_loop_failure
demo_loop_failure.main()
print()

print("="*70)
print("ALL CELLS COMPLETED SUCCESSFULLY!")
print("="*70)
print()
print(f"Output saved to: {output_file}")

# Restore stdout and close file
sys.stdout = original_stdout
log_file.close()
print(f"\nOutput saved to: {output_file}")
