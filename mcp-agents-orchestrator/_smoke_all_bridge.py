import os
import json
from _smoke_test_bridge import run

print('--- Web Search ---')
run('web_search', 'Find score', {'query':'senegal vs congo score today','max_results':5},
    permission_profile={'tool_allowlist':['mcp','mcp:stdio:npx']}, cwd=None)

print('\n--- Deep Research ---')
run('deep_research', 'Quick research', {'topic':'Senegal vs Congo match result','depth':'brief'},
    permission_profile={'tool_allowlist':['mcp','mcp:stdio:npx'], 'sandbox':'read-only'}, cwd=None)

print('\n--- RAG ---')
run('rag', 'Explain RAG', {'query':'What is Retrieval-Augmented Generation?','max_results':3},
    permission_profile={'sandbox':'read-only'}, cwd=None)

