"""
movement_flags.py — Soccer-Specific Biomechanical Movement Flag Dictionary

This module provides the structured reference library used during movement screen
analysis. It maps observed biomechanical patterns to:
  - What position groups are most impacted
  - The injury risk association
  - Corrective coaching cues

Gemini video analysis uses this as a grounding reference via the system prompt to
ensure that output flags are drawn from soccer-specific clinical vocabulary
rather than generic athletic training language.
"""

# ─── SOCCER MOVEMENT FLAG DICTIONARY ─────────────────────────────────────────
# Each entry contains the flag name, soccer context, risk level, and coaching cues.

MOVEMENT_FLAGS = {

    # ── LOWER LIMB ──────────────────────────────────────────────────────────────

    "knee_valgus": {
        "description": "Inward collapse of the knee during deceleration, landing, or squat movement.",
        "soccer_context": "Common in decelerating from sprints and cutting off the dribble. "
                          "Highest prevalence in fullbacks and wingers who change direction frequently.",
        "injury_risk": ["ACL tear", "Medial knee ligament strain", "Patellofemoral pain"],
        "risk_band": "HIGH",
        "position_flags": ["Winger", "Fullback", "Striker"],
        "coaching_cues": [
            "Drive knees out in line with the 2nd toe on landing.",
            "Focus on glute activation drills before sprint sessions (banded walks, clamshells).",
            "Use cone guides to cue outward knee track during change-of-direction drills."
        ]
    },

    "hip_drop": {
        "description": "Contralateral (opposite side) hip drops during single-leg stance or lateral movement.",
        "soccer_context": "Indicates weak hip abductors and glute medius. "
                          "Frequently seen in players returning from hamstring or groin injury. "
                          "A strong predictor of future adductor or IT band issues.",
        "injury_risk": ["IT band syndrome", "Adductor strain", "Lumbar overload"],
        "risk_band": "MED",
        "position_flags": ["All positions"],
        "coaching_cues": [
            "Prescribe single-leg glute bridge and lateral band walks.",
            "Monitor during full-pace cutting drills in training.",
            "Tape can be used to increase proprioceptive feedback at the hip during rehab."
        ]
    },

    "forward_trunk_lean": {
        "description": "Excessive forward lean of the trunk during deceleration or squat movements.",
        "soccer_context": "Indicates tight hip flexors and/or weak glutes/hamstrings. "
                          "Common in players with high high-speed running (HSR) volumes "
                          "(wingers, strikers) and those returning from international duty.",
        "injury_risk": ["Lumbar strain", "Hamstring overload", "Patellar tendinopathy"],
        "risk_band": "MED",
        "position_flags": ["Winger", "Striker", "Central Midfielder"],
        "coaching_cues": [
            "Hip flexor mobility work (kneeling lunge stretch) prescribed daily.",
            "Cue upright chest position during deceleration mechanics practice.",
            "Incorporate Romanian Deadlift (RDL) to strengthen posterior chain."
        ]
    },

    "asymmetry_lateral": {
        "description": "Player exhibits measurably different movement quality or range of motion on left vs right side.",
        "soccer_context": "Lateral asymmetry is one of the most reliable pre-injury indicators in soccer. "
                          "Players who favour their dominant foot often develop asymmetric loading "
                          "patterns that overload the weaker side over a season.",
        "injury_risk": ["Groin strain (weaker side)", "Hamstring strain", "Ankle sprain"],
        "risk_band": "HIGH",
        "position_flags": ["All positions"],
        "coaching_cues": [
            "Implement unilateral loading (single-leg press, Bulgarian split squat) with extra focus on weaker side.",
            "Use jump-landing assessment to quantify symmetry (force plate if available).",
            "Reduce asymmetric loads until <15% deficit is achieved."
        ]
    },

    "ankle_pronation_excessive": {
        "description": "Excessive inward roll of the ankle during stance or landing phase.",
        "soccer_context": "Frequent in players on hard artificial surfaces. Often precedes lateral "
                          "ankle sprains, particularly during reactive agility and in-game tackle situations.",
        "injury_risk": ["Lateral ankle sprain", "Plantar fasciitis", "Achilles tendinopathy"],
        "risk_band": "MED",
        "position_flags": ["Fullback", "Winger", "Goalkeeper"],
        "coaching_cues": [
            "Assess boot/cleat fit and insole support.",
            "Foot strengthening programme (toe curls, single-leg balance with perturbation).",
            "Monitor on artificial turf surfaces specifically."
        ]
    },

    "pelvic_tilt_anterior": {
        "description": "Anterior pelvic tilt (lumbar arch increased) observed during standing or movement patterns.",
        "soccer_context": "Common consequence of prolonged sitting combined with high sprinting loads. "
                          "Indicates hip flexor dominance and glute inhibition — a risk pattern for "
                          "groin and hip flexor strains.",
        "injury_risk": ["Hip flexor strain", "Groin strain", "Lumbar disc stress"],
        "risk_band": "MED",
        "position_flags": ["All positions"],
        "coaching_cues": [
            "Daily hip flexor stretching (couch stretch, 90/90 hip stretch) mandatory.",
            "Core activation drills focused on posterior pelvic tilt under load.",
            "Limit seated time between training sessions."
        ]
    },

    "limited_dorsiflexion": {
        "description": "Reduced ankle dorsiflexion range of motion during squat or movement screen.",
        "soccer_context": "Tight Achilles/gastroc-soleus complex. A key predictor of Achilles tendinopathy "
                          "and plantar fasciitis in players with high acceleration/deceleration demands.",
        "injury_risk": ["Achilles tendinopathy", "Plantar fasciitis", "Calf strain"],
        "risk_band": "HIGH",
        "position_flags": ["Striker", "Winger", "Fullback"],
        "coaching_cues": [
            "Calf raises on a step (both eccentric and concentric) prescribed.",
            "Ankle mobility work (half-kneeling ankle rock) before each training session.",
            "Monitor Achilles tightness post-sprint training."
        ]
    },

    "head_forward_posture": {
        "description": "Head positioned significantly forward of the shoulder line during movement.",
        "soccer_context": "Less directly linked to lower limb injury but indicates upper thoracic tightness "
                          "that can affect sprint mechanics and increase risk in aerial duel situations.",
        "injury_risk": ["Cervical strain (heading duels)", "Upper trapezius overload"],
        "risk_band": "LOW",
        "position_flags": ["Centre-Back", "Striker"],
        "coaching_cues": [
            "Thoracic mobility work (foam roller extensions, cat-camel).",
            "Chin tuck exercises to restore neutral head position.",
            "Assess heading technique with coaching staff during next session."
        ]
    },

    "knee_hyperextension": {
        "description": "Knee moves into hyperextension (beyond neutral) on landing or single-leg stance.",
        "soccer_context": "Significant ACL risk indicator. Often seen in players with hypermobility "
                          "or following incomplete neuromuscular rehabilitation from prior knee injury.",
        "injury_risk": ["ACL injury", "Posterior knee capsule strain"],
        "risk_band": "HIGH",
        "position_flags": ["All positions"],
        "coaching_cues": [
            "Mandatory neuromuscular knee stability programme (Nordic curls, single-leg squats).",
            "Cue 'soft knees' in all landing mechanics practice.",
            "Refer to physio for comprehensive knee stability screen immediately."
        ]
    },

    "trunk_rotation_asymmetry": {
        "description": "Asymmetric trunk rotation during movement, with one side rotating significantly more.",
        "soccer_context": "Common in players who heavily favour one-footed movements (e.g. driving crosses "
                          "or shooting predominantly off one leg). Can lead to oblique and lumbar overload over time.",
        "injury_risk": ["Oblique strain", "Lumbar rotation stress fracture risk"],
        "risk_band": "MED",
        "position_flags": ["Winger", "Fullback", "Central Midfielder"],
        "coaching_cues": [
            "Incorporate bilateral movement patterns into technical training.",
            "Prescribe thoracic rotation mobility (seated rotation stretch).",
            "Monitor lumbar region during and after high-rotation match weeks."
        ]
    }
}

# ─── POSITION RISK SUMMARY ─────────────────────────────────────────────────────
# Pre-compiled mapping of which flags are most relevant by position.
# Used to narrow the Gemini prompt focus for efficiency.

POSITION_FLAG_PRIORITY = {
    "Winger": ["knee_valgus", "asymmetry_lateral", "forward_trunk_lean", "ankle_pronation_excessive", "trunk_rotation_asymmetry"],
    "Fullback": ["knee_valgus", "ankle_pronation_excessive", "hip_drop", "limited_dorsiflexion"],
    "Striker": ["knee_valgus", "forward_trunk_lean", "pelvic_tilt_anterior", "limited_dorsiflexion"],
    "Central Midfielder": ["forward_trunk_lean", "hip_drop", "trunk_rotation_asymmetry", "pelvic_tilt_anterior"],
    "Defensive Midfielder": ["hip_drop", "pelvic_tilt_anterior", "knee_hyperextension"],
    "Centre-Back": ["hip_drop", "head_forward_posture", "knee_valgus", "asymmetry_lateral"],
    "Goalkeeper": ["ankle_pronation_excessive", "knee_hyperextension", "asymmetry_lateral"]
}

def get_flags_for_position(position: str) -> list:
    """Returns the ordered list of movement flag IDs to prioritize for a given position."""
    return POSITION_FLAG_PRIORITY.get(position, list(MOVEMENT_FLAGS.keys()))

def get_flag_detail(flag_id: str) -> dict:
    """Returns the full detail dict for a given flag ID."""
    return MOVEMENT_FLAGS.get(flag_id, {})

def build_movement_screen_context(position: str) -> str:
    """
    Builds a focused system context string for the Gemini movement analysis prompt,
    prioritizing flags most relevant to the player's position.
    This text is injected into the movement_system.txt prompt at call time.
    """
    priority_flags = get_flags_for_position(position)
    context = f"For a {position}, prioritize checking for the following mechanical risks:\n\n"
    for flag_id in priority_flags:
        flag = MOVEMENT_FLAGS.get(flag_id, {})
        context += f"- **{flag_id.replace('_', ' ').title()}**: {flag.get('description', '')}\n"
        context += f"  Injury risks: {', '.join(flag.get('injury_risk', []))}\n"
        context += f"  Cues: {'; '.join(flag.get('coaching_cues', []))}\n\n"
    return context
