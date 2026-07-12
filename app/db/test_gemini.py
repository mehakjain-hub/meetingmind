from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

transcript = """Speaker SPEAKER_00: of the research company we contracted to carry out the work. The MISRAEUS will arrive at 11.30, so I plan to break at about 11.15 to give her time to set up. It may also mean that we need to interrupt the first few agenda items, but we'll come back to those. OK, so item one is relocation and plans for flexible working. Now, as you know, Paul and his team have been working on plans to extend flexible working hours across the company. So, Paul, perhaps I can begin by asking you to fill us in on your progress. Sure, thanks."""

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents=f"Summarize this meeting transcript in one paragraph:\n\n{transcript}"
)

print(response.text)