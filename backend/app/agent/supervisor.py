MAX_TURNS = 4
DRAFT_WORDS = ('신청서', '초안')

def pick_worker(state: dict) -> str:
    if state.get('turns', 0) >= MAX_TURNS:
        return 'finish'
    if 'sources' not in state:
        return 'search'
    if any((w in state['question'] for w in DRAFT_WORDS)) and state.get('sources') and ('draft' not in state):
        return 'draft'
    return 'finish'
