from niyet.allocator import allocate
from niyet.optimizer import global_allocate
from niyet.types import CandidateMatch, IntentType, Responder


responders = [
    Responder("r1", ("control",), (IntentType.ASK,), 1),
    Responder("r2", ("robotics",), (IntentType.ASK,), 1),
]

matches = [
    CandidateMatch("general-robotics", "r1", 0.99, 0.99, 0.99),
    CandidateMatch("general-robotics", "r2", 0.98, 0.98, 0.98),
    CandidateMatch("control-question", "r1", 0.97, 0.97, 0.97),
    CandidateMatch("control-question", "r2", 0.10, 0.10, 0.10),
]

for name, assignments in {
    "greedy": allocate(matches, responders),
    "global": global_allocate(matches, responders),
}.items():
    print(name)
    for assignment in assignments:
        print(
            f"  {assignment.intent_id:20} -> {assignment.responder_id} "
            f"score={assignment.score:.2f}"
        )
    print(f"  total utility: {sum(item.score for item in assignments):.2f}")
