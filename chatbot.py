import streamlit as st
import time
import os
from groq import Groq

#Using API Key
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

#Instructions
default_agents = {
    "Judge": "You are a fair and wise judge in a courtroom. You have to listen to all the sides and then deliver a reasoned and fair verdict.",
    "Prosecution Lawyer": "You are the prosecution lawyer. You have to present the case against the defendant based on the provided case summary.",
    "Defense Lawyer": "You are the defense lawyer. You have to argue in defense of your client using legal reasoning and facts from the case summary.",
    "Plaintiff": "You are the plaintiff in this case. You have to explain your complaint and what you expect from the court.",
    "Defendant": "You are the defendant. You have toxplain your side of the story and why you believe you are not at fault."
}

#Trial Phases
base_phases = [
    ("Opening Statements", ["Plaintiff", "Prosecution Lawyer", "Defendant", "Defense Lawyer"]),
    ("Witness Interrogation & Argumentation", []),  
    ("Closing Statements", ["Prosecution Lawyer", "Defense Lawyer"]),
    ("Judge’s Ruling", ["Judge"])
]

#Done to avoid 6000 tokens error of groq
def trim_context(context, max_chars=6000):
    if len(context) > max_chars:
        return context[-max_chars:]
    return context

def trim_case_summary(summary, max_chars=2000):
    if len(summary) > max_chars:
        return summary[:max_chars] + " ...[truncated]"
    return summary

#Streamlit UI
st.set_page_config(page_title="Courtroom Simulation", layout="wide")
st.title("AI Courtroom Simulation")

with st.sidebar:
    st.markdown("### Simulation Settings")
    case_summary = st.text_area("Enter Case Summary", height=200, placeholder="Paste your case preview here...")

    st.markdown("---")
    st.markdown("### Add Custom Roles with Phase Assignment")

    if "custom_roles" not in st.session_state:
        st.session_state.custom_roles = {}  #Format: {role: (instruction, [phases], witness_side)}

    new_role = st.text_input("Role Name")
    new_instruction = st.text_area("Role Instruction")
    available_phases = [p[0] for p in base_phases]
    
    #Witness controls
    is_witness = st.checkbox("Is this role a witness?")
    witness_side = None
    if is_witness:
        selected_phases = ["Witness Interrogation & Argumentation"]
        witness_side = st.radio("Calling Side", ["Prosecution", "Defense", "Neutral"], horizontal=True)

    if st.button("Add Role"):
        if new_role and new_instruction and selected_phases and is_witness and not witness_side:
            st.warning("Witnesses must have a calling side (Prosecution/Defense/Neutral)")
        elif new_role and new_instruction and selected_phases:
            st.session_state.custom_roles[new_role] = (
                new_instruction, 
                selected_phases,
                witness_side if is_witness else None
            )
            st.success(f"Added {new_role} to phases: {', '.join(selected_phases)}")
        else:
            st.warning("Please enter role name, instruction, and select at least one phase.")

    if st.session_state.custom_roles:
        if st.button("Clear All Custom Roles"):
            st.session_state.custom_roles.clear()
            st.success("Cleared all custom roles.")

    if st.button("Run Simulation"):
        if case_summary.strip() != "":
            st.session_state.run_sim = True
            st.session_state.context = ""
            st.session_state.transcript = []
        else:
            st.warning(" Please enter a case summary to begin.")

#Agent Management
def get_all_agents():
    agents = default_agents.copy()
    for role, (instruction, _, _) in st.session_state.get("custom_roles", {}).items():
        agents[role] = instruction
    return agents

def get_witnesses_by_side(side):
    return [role for role, (_, _, w_side) in st.session_state.custom_roles.items() if w_side == side]

#Generate Agent Response
def generate(role, case_summary, context, phase_name):
    agents = get_all_agents()
    instruction = agents.get(role, 'Behave appropriately for your role.')
    
    #Enhance witness instructions
    witness_side = st.session_state.custom_roles.get(role, (None, None, None))[2]
    if witness_side:
        instruction += f"\nYou are a witness called by the {witness_side}. Answer questions truthfully based on the case summary."
        if witness_side == "Neutral":
            instruction += " You are a neutral expert - remain impartial and factual."

    #Add closing statement restrictions
    if phase_name == "Closing Statements" and role in ["Prosecution Lawyer", "Defense Lawyer"]:
        instruction += (
            "\nIMPORTANT: During closing statements, you may NOT question witnesses, introduce new evidence, or refer to facts not already in evidence. "
            "You must only summarize your side's case and argue how the evidence supports your position. "
            "Address your argument to the judge (or jury) and do not ask questions of witnesses or other parties."
        )

    if role == "Judge" and phase_name == "Judge’s Ruling":
        instruction += "\nMake sure to clearly state the final verdict: 'The court finds the defendant GUILTY/NOT GUILTY.'"

    # Trim context and case summary to avoid token overflow
    trimmed_context = trim_context(context, max_chars=6000)
    trimmed_summary = trim_case_summary(case_summary, max_chars=2000)

    prompt = f"""You are participating in a simulated courtroom trial.

Case Summary:
{trimmed_summary}

Phase: {phase_name}
Role: {role}
Instructions: {instruction}

Context so far:
{trimmed_context}

IMPORTANT:
- Stay strictly within your role's perspective
- Do not improvise for other roles
- Follow proper courtroom procedure

{role}: What would you say next?
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

#Simulation Execution
if "run_sim" in st.session_state and st.session_state.run_sim and case_summary.strip() != "":
    with st.spinner("Simulating courtroom..."):
        context = st.session_state.context
        transcript = st.session_state.transcript

        for phase_name, roles in base_phases:
            if phase_name == "Witness Interrogation & Argumentation":
                st.subheader("Witness Interrogation & Argumentation")
                
                #Prosecution Witnesses
                for witness in get_witnesses_by_side("Prosecution"):
                    with st.expander(f"Prosecution Direct: {witness}", expanded=True):
                        prosecution_q = generate("Prosecution Lawyer", case_summary, 
                                               f"{context}\nYou are questioning your witness {witness}. Ask a direct question.", 
                                               "Witness Interrogation & Argumentation")
                        st.markdown(f"**Prosecution Lawyer:** {prosecution_q}")
                        context += f"\nProsecution Lawyer: {prosecution_q}\n"
                        transcript.append(("Witness Interrogation", "Prosecution Lawyer", prosecution_q))

                        witness_response = generate(witness, case_summary, context, "Witness Interrogation & Argumentation")
                        st.markdown(f"**{witness}:** {witness_response}")
                        context += f"\n{witness}: {witness_response}\n"
                        transcript.append(("Witness Interrogation", witness, witness_response))

                    with st.expander(f"Defense Cross: {witness}", expanded=True):
                        defense_q = generate("Defense Lawyer", case_summary, 
                                           f"{context}\nYou are cross-examining {witness}. Ask a challenging question.", 
                                           "Witness Interrogation & Argumentation")
                        st.markdown(f"**Defense Lawyer:** {defense_q}")
                        context += f"\nDefense Lawyer: {defense_q}\n"
                        transcript.append(("Witness Interrogation", "Defense Lawyer", defense_q))

                        witness_response = generate(witness, case_summary, context, "Witness Interrogation & Argumentation")
                        st.markdown(f"**{witness}:** {witness_response}")
                        context += f"\n{witness}: {witness_response}\n"
                        transcript.append(("Witness Interrogation", witness, witness_response))

                #Defense Witnesses
                for witness in get_witnesses_by_side("Defense"):
                    with st.expander(f"Defense Direct: {witness}", expanded=True):
                        defense_q = generate("Defense Lawyer", case_summary, 
                                           f"{context}\nYou are questioning your witness {witness}. Ask a direct question.", 
                                           "Witness Interrogation & Argumentation")
                        st.markdown(f"**Defense Lawyer:** {defense_q}")
                        context += f"\nDefense Lawyer: {defense_q}\n"
                        transcript.append(("Witness Interrogation", "Defense Lawyer", defense_q))

                        witness_response = generate(witness, case_summary, context, "Witness Interrogation & Argumentation")
                        st.markdown(f"**{witness}:** {witness_response}")
                        context += f"\n{witness}: {witness_response}\n"
                        transcript.append(("Witness Interrogation", witness, witness_response))

                    with st.expander(f"Prosecution Cross: {witness}", expanded=True):
                        prosecution_q = generate("Prosecution Lawyer", case_summary, 
                                               f"{context}\nYou are cross-examining {witness}. Ask a challenging question.", 
                                               "Witness Interrogation & Argumentation")
                        st.markdown(f"**Prosecution Lawyer:** {prosecution_q}")
                        context += f"\nProsecution Lawyer: {prosecution_q}\n"
                        transcript.append(("Witness Interrogation", "Prosecution Lawyer", prosecution_q))

                        witness_response = generate(witness, case_summary, context, "Witness Interrogation & Argumentation")
                        st.markdown(f"**{witness}:** {witness_response}")
                        context += f"\n{witness}: {witness_response}\n"
                        transcript.append(("Witness Interrogation", witness, witness_response))

                #Neutral Witnesses
                for witness in get_witnesses_by_side("Neutral"):
                    with st.expander(f"Neutral Witness: {witness}", expanded=True):
                        # Prosecution questions first
                        prosecution_q = generate("Prosecution Lawyer", case_summary, 
                                               f"{context}\nYou are questioning the neutral witness {witness}. Ask a factual question.", 
                                               "Witness Interrogation & Argumentation")
                        st.markdown(f"**Prosecution Lawyer:** {prosecution_q}")
                        context += f"\nProsecution Lawyer: {prosecution_q}\n"
                        transcript.append(("Witness Interrogation", "Prosecution Lawyer", prosecution_q))

                        witness_response = generate(witness, case_summary, context, "Witness Interrogation & Argumentation")
                        st.markdown(f"**{witness}:** {witness_response}")
                        context += f"\n{witness}: {witness_response}\n"
                        transcript.append(("Witness Interrogation", witness, witness_response))

                        #Defense questions next
                        defense_q = generate("Defense Lawyer", case_summary, 
                                           f"{context}\nYou are questioning the neutral witness {witness}. Ask a clarifying question.", 
                                           "Witness Interrogation & Argumentation")
                        st.markdown(f"**Defense Lawyer:** {defense_q}")
                        context += f"\nDefense Lawyer: {defense_q}\n"
                        transcript.append(("Witness Interrogation", "Defense Lawyer", defense_q))

                        witness_response = generate(witness, case_summary, context, "Witness Interrogation & Argumentation")
                        st.markdown(f"**{witness}:** {witness_response}")
                        context += f"\n{witness}: {witness_response}\n"
                        transcript.append(("Witness Interrogation", witness, witness_response))
            else:
                st.subheader(f" {phase_name}")
                for role in roles:
                    with st.expander(f"{role}'s Turn", expanded=True):
                        response = generate(role, case_summary, context, phase_name)
                        st.markdown(f"**{role}:** {response}")
                        context += f"\n{role}: {response}\n"
                        transcript.append((phase_name, role, response))
                        time.sleep(0.5)

        st.success("Simulation Complete!")
        transcript_text = "\n".join([f"[{p}] {r}: {t}" for p, r, t in transcript])
        st.download_button("Download Transcript", data=transcript_text, file_name="courtroom_transcript.txt")

elif "run_sim" in st.session_state and not case_summary.strip():
    st.warning(" Please enter a case summary to begin.")
