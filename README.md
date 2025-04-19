
# AI Courtroom Simulation
An interactive courtroom trial simulation powered by Streamlit and Groq's LLaMA 3 model. This app allows users to enter a case summary and, define courtroom roles (including custom witnesses).


## Features
 Role-Specific Reasoning: Roles like Judge, Prosecution, Defense, Plaintiff, and Defendant follow realistic legal behavior.

 Custom Roles and Witnesses: Add custom participants and witnesses with role-specific instructions and assign them to trial phases.

Dynamic Phases: Includes phases like:

Opening Statements

Witness Interrogation & Argumentation

Closing Statements

Judge’s Final Ruling

Context Trimming: Keeps interactions within token limits while retaining relevant context.

Transcript Download: Save a detailed transcript of the entire trial simulation.


## Customization
Add custom roles from the sidebar:

1) Enter role name (e.g., "Forensic Expert")

2) Add instructions for how this role should behave.

3) Mark them as a witness if needed, and specify which side is calling them.

4) Add them to the "Witness Interrogation" phase.


# Workflow
This section outlines the end-to-end workflow of how your courtroom simulation system operates, from user input to final verdict, including technical and logic-level processes.

## 1. Initialization


- Groq API Setup: 

The app initializes a Groq API client using the provided API key and sets the LLaMA 3 model (llama3-70b-8192).

- Session State Creation: 

Persistent data like chat logs, case description, roles, phase index, and dynamic role settings are initialized via st.session_state.

## 2. Case Input & Role Configuration
### Case Description:-

The user inputs a text summary of the legal case.

This summary is used in every prompt to provide context for the language model.

### Role Setup
The app defines default roles: Judge, Prosecution Lawyer, Defense Lawyer, Plaintiff, and Defendant.

Each role is associated with:

- A system instruction (e.g., behave like a lawyer)

- A participant label (e.g., “Defense Lawyer”)

- The trial phases they can act in

### Add Custom Roles
User can dynamically add roles (e.g., Witnesses) using input fields in the sidebar.

For each custom role, the user provides:

- Role Name (e.g., “Forensic Expert”)

- Behavior Instruction (e.g., “Speak only about the forensic report”)

- Active Phases (select from trial phases)

- These roles are stored in session state and included in the simulation loop.

## 3. Trial Phase Workflow
The simulation proceeds through the following ordered phases:

- Opening Statements

- Witness Interrogation & Argumentation

- Closing Statements

- Judge’s Ruling

- Each phase has rules about which agents may participate and what kind of responses are appropriate.

## 4. Contextual Prompting & Generation
### Prompt Construction
For each role’s turn, the system constructs a prompt combining:

- Case description

- Role-specific instruction (from system message)

- Previous chat history (with token-trim logic)

- User-defined constraints (e.g., no new facts in closing)

- Current trial phase and role turn

### Groq API Call
- The prompt is sent to the Groq client to generate a response from LLaMA 3.

- Output is parsed and appended to the session’s chat_log.

## 5. Phase-wise Role Turn Control
- The app checks which roles are active in the current phase.

- It iterates over those roles one-by-one and generates their output using the LLM.

- For custom roles like witnesses:

  -  If categorized as prosecution or defense, appropriate lawyer questions them

  - Cross-examination is performed by the opposing lawyer

## 6. Closing the Trial
### Judge’s Verdict

In the final phase, the Judge role synthesizes the entire case, reviews arguments, and generates a final ruling.

## 7. Transcript Generation
The user can click “Download Transcript” to download the complete trial history.

All agent dialogues are formatted into a .txt file containing:

- Case summary

- Turn-by-turn courtroom dialogue

- Final ruling

