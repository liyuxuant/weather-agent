import json

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from linkedin_jobs import search_linkedin_jobs


@tool
def search_linkedin_jobs_tool(
    keyword: str,
    limit: int = 5,
) -> str:
    """
    Search LinkedIn for jobs.

    Use this tool when the user asks to find or search
    for jobs on LinkedIn.

    Args:
        keyword:
            The job title or search keyword.
            Example: "Java Engineer"

        limit:
            Number of jobs to return.
            Default is 5.
    """

    print(
        f"\n[Tool] Searching LinkedIn for "
        f"{limit} '{keyword}' jobs..."
    )

    jobs = search_linkedin_jobs(
        keyword=keyword,
        limit=limit,
    )

    if not jobs:
        return (
            f"No LinkedIn jobs were found "
            f"for '{keyword}'."
        )

    return json.dumps(
        jobs,
        indent=2,
    )


model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)


weather_agent = create_agent(
    model=model,
    tools=[
        search_linkedin_jobs_tool,
    ],
    system_prompt="""
You are a browser-enabled job search assistant.

Your job is to understand what the user wants
and decide whether to use the LinkedIn job search tool.

Rules:

1. If the user asks to search for jobs on LinkedIn,
   use search_linkedin_jobs_tool.

2. Extract the job keyword from the user's request.

3. Extract the number of requested jobs.
   If the user does not specify a number, use 5.

4. Do not invent job results.

5. Only report jobs returned by the tool.

6. Present job results clearly with:
   - job title
   - LinkedIn URL

7. If the user asks about something unrelated to
   LinkedIn job searching, explain that this agent
   currently supports LinkedIn job searches.

Examples:

User:
Find me 3 Python Developer jobs on LinkedIn.

Tool call:
keyword = "Python Developer"
limit = 3

User:
Search LinkedIn for Java Engineer jobs.

Tool call:
keyword = "Java Engineer"
limit = 5
""",
)