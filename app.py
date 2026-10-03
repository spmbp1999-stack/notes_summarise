"""Launch with: python -m streamlit run app.py"""

import json
import os

import streamlit as st

from examples import EXAMPLES
from notes_engine import (
    NotesError,
    count_words,
    export_notes,
    generate_notes,
)

st.set_page_config(
    page_title="Smart Study Notes Generator",
    page_icon="📘",
    layout="wide",
)

st.title("📘 Smart Study Notes Generator")
st.caption("Generate a concise summary, key points, and word-count statistics.")

with st.sidebar:
    st.header("Settings")

entered_key = st.text_input(
        "OpenAI API key",
        type="password",
        help="Never included in downloaded notes or test records.",
    )

api_key = entered_key.strip() or os.environ.get("OPENAI_API_KEY", "")

st.caption(
        "API key configured."
        if api_key
        else "Enter an API key to generate notes."
    )

length = st.selectbox(
        "Summary length",
        ["Balanced — 40%", "Brief — 25%", "Detailed — 55%"],
    )

ratio = {
        "Balanced — 40%": 0.40,
        "Brief — 25%": 0.25,
        "Detailed — 55%": 0.55,
    }[length]

st.info(
        "Requires internet access and available API quota. "
        "API usage may incur charges."
    )

st.caption(
        "Submitted text is sent to OpenAI. "
        "Do not submit sensitive information. "
        "A word-limit retry may make one additional request per paragraph."
    )

if st.button("Clear generated results"):
        for name in ("result", "test_records"):
            st.session_state.pop(name, None)

for name in list(st.session_state):
            if name.startswith("review_"):
                del st.session_state[name]

st.rerun()

def display_result(result, download_key):
    first, second, third = st.columns(3)
first.metric("Original words", result["original_words"])
    second.metric("Summary words", result["summary_words"])
    third.metric(
        "Text reduced",
        f"{result['reduction_percent']:.2f}%",
    )
first.metric("Original words", result["original_words"])
    second.metric("Summary words", result["summary_words"])
    third.metric(
        "Text reduced",
        f"{result['reduction_percent']:.2f}%",
    )

st.subheader("Summary")
    st.write(result["summary"])

st.subheader("Key points")
    st.table(
        [
            {"Point": number, "Study note": point}
            for number, point in enumerate(result["key_points"], start=1)
        ]
    )

with st.expander("Original paragraph and generation details"):
        st.write(result["original"])
        st.caption(
            f"Model: {result['model']} | "
            f"Generated UTC: {result['generated_at_utc']} | "
            f"API requests: {result['api_requests']}"
        )

st.download_button(
        "Download notes",
        data=export_notes(result),
        file_name="study_notes.txt",
        mime="text/plain",
        key=download_key,
    )

generate_tab, test_tab, about_tab = st.tabs(
    ["Generate notes", "Three-paragraph test lab", "About"]
)

with generate_tab:
    selected = st.selectbox(
        "Sample paragraph",
        [example["title"] for example in EXAMPLES],
    )

if st.button("Load selected sample"):
        st.session_state["paragraph"] = next(
            example["text"]
            for example in EXAMPLES
            if example["title"] == selected
        )

paragraph = st.text_area(
        "Enter your English paragraph",
        key="paragraph",
        height=240,
        max_chars=30000,
        placeholder="Paste between 30 and 3,000 words here...",
    )

st.caption(f"Input word count: {count_words(paragraph)}")

consent = st.checkbox(
        "Send this paragraph to OpenAI to generate study notes."
    )

if st.button(
        "Generate study notes",
        type="primary",
        disabled=not consent,
    ):
        st.session_state.pop("result", None)

try:
            with st.spinner("Generating summary and key points..."):
                st.session_state["result"] = generate_notes(
                    paragraph,
                    api_key,
                    ratio,
                )
        except NotesError as error:
            st.error(str(error))

if "result" in st.session_state:
        result = st.session_state["result"]

if paragraph.strip() != result["original"]:
            st.info(
                "Showing the previous result. "
                "Generate again to summarize the edited paragraph."
            )

display_result(result, "download_single")

st.warning(
        "AI-generated notes may omit details or contain mistakes. "
        "Check them against the original paragraph."
    )

with test_tab:
    st.subheader("Run three real model tests")

st.write(
        "The app sends each sample paragraph to the model, records its "
        "actual output, and calculates the statistics. "
        "No pre-written summaries are substituted."
    )

st.table(
        [
            {
                "Test": number,
                "Topic": example["title"],
                "Original words": count_words(example["text"]),
            }
            for number, example in enumerate(EXAMPLES, start=1)
        ]
    )

batch_consent = st.checkbox(
        "Send all three sample paragraphs to OpenAI. "
        "API usage may incur charges."
    )

if st.button(
        "Run all 3 tests",
        type="primary",
        disabled=not batch_consent,
    ):
        if not api_key:
            st.error("Enter your API key in the sidebar first.")
        else:
            st.session_state["test_records"] = []

for name in list(st.session_state):
                if name.startswith("review_"):
                    del st.session_state[name]

progress = st.progress(0)

for index, example in enumerate(EXAMPLES):
                record = {
                    **example,
                    "observation": "",
                }

try:
                    with st.spinner(f"Testing {example['title']}..."):
                        record["result"] = generate_notes(
                            example["text"],
                            api_key,
                            ratio,
                        )
                    record["status"] = "success"

except NotesError as error:
                    record["status"] = "error"
                    record["error"] = str(error)

st.session_state["test_records"].append(record)
                progress.progress((index + 1) / len(EXAMPLES))

records = st.session_state.get("test_records", [])

if records:
        st.table(
            [
                {
                    "Topic": record["title"],
                    "Status": record["status"],
                    "Original words": count_words(record["text"]),
                    "Summary words": record.get("result", {}).get(
                        "summary_words"
                    ),
                    "Reduction (%)": record.get("result", {}).get(
                        "reduction_percent"
                    ),
                }
                for record in records
            ]
        )

for index, record in enumerate(records):
            with st.expander(record["title"], expanded=True):
                if record["status"] == "success":
                    display_result(
                        record["result"],
                        f"download_test_{index}",
                    )

st.caption("Review focus: " + record["review_focus"])

record["observation"] = st.text_area(
                        "Observation: relevance, coherence, and omissions",
                        key=f"review_{index}",
                        placeholder=(
                            "Compare the original and summary. "
                            "What was retained or omitted? "
                            "Does the summary read naturally?"
                        ),
                    )
                else:
                    st.error(record["error"])

st.caption(
            "After typing an observation, click outside its field "
            "before downloading so the latest text is included."
        )

st.download_button(
            "Download recorded outputs — JSON",
            data=json.dumps(records, indent=2, ensure_ascii=False),
            file_name="recorded_outputs.json",
            mime="application/json",
        )

sections = []

for record in records:
            section = (
                record["title"]
                + "\n"
                + "=" * len(record["title"])
                + "\n\n"
            )

if record["status"] == "success":
                section += export_notes(record["result"])
                section += (
                    "\nObservation: "
                    + (
                        record["observation"].strip()
                        or "Not yet reviewed."
                    )
                    + "\n"
                )
            else:
                section += "Test failed: " + record["error"] + "\n"

sections.append(section)

st.download_button(
            "Download submission record — TXT",
            data="\n\n".join(sections),
            file_name="mini_project_test_record.txt",
            mime="text/plain",
        )

with about_tab:
    st.subheader("Aim")
    st.write(
        "Develop a Python application that generates a short summary "
        "and key points from a paragraph using a pre-trained "
        "Generative AI model."
    )

st.subheader("Reduction calculation")
    st.latex(
        r"\text{Reduction (\%)} = "
        r"\frac{W_{\text{original}} - W_{\text{summary}}}"
        r"{W_{\text{original}}} \times 100"
    )

st.write(
        "Only summary words are included in the reduction calculation. "
        "Key points are excluded. Python counts both texts using the "
        "same rule; the model does not calculate the statistics."
    )

st.subheader("Summary length")
    st.write(
        "The selected percentage is a maximum word target. "
        "If the model exceeds it, the application retries once. "
        "It never cuts a sentence simply to satisfy the limit."
    )

st.subheader("Evaluation")
    st.write(
        "Relevance: Does the summary preserve the main ideas without "
        "adding unsupported information? "
        "Coherence: Are the sentences clear, connected, and readable? "
        "A higher reduction percentage does not necessarily mean "
        "a better summary."
    )

st.subheader("Privacy and limitations")
    st.write(
        "The app does not automatically save your key or paragraph "
        "to local files. Generated results remain in session memory "
        "until cleared or the session ends. Download results before "
        "closing the application. Submitted text is processed by OpenAI "
        "under its API data policies. The store=False setting does not "
        "guarantee zero provider retention. This project is intended "
        "for local educational use, not an unauthenticated public service."
    )
