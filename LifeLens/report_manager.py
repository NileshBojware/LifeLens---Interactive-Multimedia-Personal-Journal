"""
LifeLens - Report & Analytical Conclusion Manager
Generates comprehensive Weekly, Monthly, and All-Time reports with:
- Algorithmic Wellness & Psychological Conclusion Engine
- Activity-Energy Correlations & Behavioral Insights
- Burnout & Fatigue Risk Assessment
- Actionable Lifestyle Prescriptions
- Interactive Print & PDF Export (Offline HTML & Text formats)
"""

import os
import sys
import json
import math
import webbrowser
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from data_manager import (
    load_entries,
    MOOD_MAP,
    ACTIVITIES,
    DATA_DIR,
    ensure_data_directories,
    PERSONALITY_THEMES,
    get_active_personality,
)

REPORTS_DIR = os.path.join(DATA_DIR, "reports")


def ensure_reports_dir():
    """Ensure the reports output directory exists."""
    ensure_data_directories()
    os.makedirs(REPORTS_DIR, exist_ok=True)


# Mood Valence Weights for Clinical/Behavioral Scoring
MOOD_VALENCE = {
    "Happy": 10.0,
    "Good": 8.0,
    "Calm": 8.5,
    "Neutral": 5.0,
    "Tired": 3.5,
    "Stressed": 2.5,
    "Sad": 1.5,
}


def parse_entry_date(date_str):
    """Safely parse entry date string into date object."""
    if not date_str:
        return datetime.now().date()
    try:
        return datetime.strptime(date_str.strip()[:10], "%Y-%m-%d").date()
    except Exception:
        try:
            return datetime.fromisoformat(date_str.strip()).date()
        except Exception:
            return datetime.now().date()


def filter_entries_by_period(entries, period="weekly"):
    """
    Filters entries according to the chosen period.
    Period options:
      - 'weekly': Last 7 days (or 7-day window ending at newest entry)
      - 'monthly': Last 30 days (or 30-day window ending at newest entry)
      - 'all': All entries in cartridge
    Returns: (filtered_entries, period_label, start_date, end_date, is_anchored_to_latest)
    """
    if not entries:
        today = datetime.now().date()
        return [], "No Entries Available", today, today, False

    # Sort ascending by date
    sorted_entries = sorted(entries, key=lambda x: parse_entry_date(x.get("date", "")))
    today = datetime.now().date()

    if period == "all":
        start_d = parse_entry_date(sorted_entries[0].get("date", ""))
        end_d = parse_entry_date(sorted_entries[-1].get("date", ""))
        label = f"Full Cartridge Record ({start_d.strftime('%b %d, %Y')} – {end_d.strftime('%b %d, %Y')})"
        return sorted_entries, label, start_d, end_d, False

    days_span = 7 if period == "weekly" else 30
    cutoff_today = today - timedelta(days=days_span - 1)

    # First attempt: Check entries in the strict [today - span, today]
    recent_entries = [e for e in sorted_entries if parse_entry_date(e.get("date", "")) >= cutoff_today]

    if recent_entries:
        start_d = cutoff_today
        end_d = today
        period_title = "Weekly Report (Recent 7 Days)" if period == "weekly" else "Monthly Report (Recent 30 Days)"
        label = f"{period_title}: {start_d.strftime('%b %d, %Y')} – {end_d.strftime('%b %d, %Y')}"
        return recent_entries, label, start_d, end_d, False

    # Second attempt: Anchor to the newest entry's date if student entries were logged earlier
    latest_date = parse_entry_date(sorted_entries[-1].get("date", ""))
    anchor_start = latest_date - timedelta(days=days_span - 1)
    anchored_entries = [e for e in sorted_entries if parse_entry_date(e.get("date", "")) >= anchor_start]

    if not anchored_entries:
        # Fallback to last N entries if span has sparse dates
        anchored_entries = sorted_entries[-min(len(sorted_entries), 7 if period == "weekly" else 30):]

    start_d = parse_entry_date(anchored_entries[0].get("date", ""))
    end_d = parse_entry_date(anchored_entries[-1].get("date", ""))
    period_title = "Weekly Report (Last Active Week)" if period == "weekly" else "Monthly Report (Last Active Month)"
    label = f"{period_title}: {start_d.strftime('%b %d, %Y')} – {end_d.strftime('%b %d, %Y')}"
    return anchored_entries, label, start_d, end_d, True


def generate_report_data(period="weekly"):
    """
    Deep Behavioral & Psychological Report Analysis Engine.
    Synthesizes entries into quantifiable scores and explicit qualitative conclusions.
    """
    all_entries = load_entries()
    filtered_entries, period_label, start_date, end_date, is_anchored = filter_entries_by_period(all_entries, period)
    total_count = len(filtered_entries)

    if total_count == 0:
        return {
            "period": period,
            "period_label": period_label,
            "total_entries": 0,
            "has_data": False,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "conclusion_title": "INSUFFICIENT LOG DATA",
            "conclusion_verdict": "NO DATA LOGGED",
            "conclusion_badge_color": "#64748b",
            "wellness_score": 0,
            "executive_summary": "No journal entries were found for the selected time horizon. Please record entries to synthesize analytical conclusions.",
            "recommendations": ["Log at least 3 daily journal entries to unlock algorithmic insights."],
            "activity_impacts": [],
            "entries": []
        }

    # 1. Fundamental Averages & Distribution
    energies = [int(e.get("energy", 5)) for e in filtered_entries]
    avg_energy = round(sum(energies) / total_count, 1)

    # Standard deviation of energy (stability / volatility indicator)
    variance = sum((x - avg_energy) ** 2 for x in energies) / total_count
    energy_std_dev = math.sqrt(variance)

    mood_counts = {m: 0 for m in MOOD_MAP.keys()}
    activity_counts = {}
    activity_energy = {}
    activity_moods = {}

    for e in filtered_entries:
        m = e.get("mood", "Good")
        act = e.get("activity", "Other")
        en = int(e.get("energy", 5))

        mood_counts[m] = mood_counts.get(m, 0) + 1
        activity_counts[act] = activity_counts.get(act, 0) + 1

        if act not in activity_energy:
            activity_energy[act] = []
            activity_moods[act] = []
        activity_energy[act].append(en)
        activity_moods[act].append(m)

    top_mood = max(mood_counts.items(), key=lambda x: x[1])[0]
    top_mood_emoji = MOOD_MAP.get(top_mood, {}).get("emoji", "😊")
    top_activity = max(activity_counts.items(), key=lambda x: x[1])[0]

    # 2. Wellness Index & Vitality Score (0-100)
    total_valence = sum(MOOD_VALENCE.get(e.get("mood", "Good"), 5.0) for e in filtered_entries)
    avg_valence = total_valence / total_count  # 0 to 10
    wellness_score = int(round(0.55 * (avg_valence * 10) + 0.45 * (avg_energy * 10)))
    wellness_score = max(5, min(100, wellness_score))

    # Determine Verdict Grade and Classification
    if wellness_score >= 82:
        verdict = "OPTIMAL & VIBRANT (Grade A+)"
        verdict_status = "High Emotional Vitality & Peak Stamina"
        badge_color = "#10b981"  # Emerald
        verdict_emoji = "🌟"
    elif wellness_score >= 68:
        verdict = "STABLE & BALANCED (Grade A)"
        verdict_status = "Positive Baseline & Healthy Resilience"
        badge_color = "#0284c7"  # Sky Blue
        verdict_emoji = "🌿"
    elif wellness_score >= 50:
        verdict = "MODERATE EQUILIBRIUM (Grade B)"
        verdict_status = "Functional Day-to-Day with Minor Fluctuations"
        badge_color = "#f59e0b"  # Amber
        verdict_emoji = "⚖️"
    elif wellness_score >= 35:
        verdict = "ELEVATED STRAIN / FATIGUE (Grade C)"
        verdict_status = "Fatigue Build-up & Energy Deficit Detected"
        badge_color = "#ea580c"  # Orange
        verdict_emoji = "⚠️"
    else:
        verdict = "STRESS & BURNOUT ALERT (Grade D)"
        verdict_status = "Prolonged Exhaustion; Decompression Urged"
        badge_color = "#ef4444"  # Red
        verdict_emoji = "🚨"

    # 3. Energy Trajectory (Oscillation Trend)
    if total_count >= 2:
        mid = total_count // 2
        first_half_avg = sum(energies[:mid]) / mid
        second_half_avg = sum(energies[mid:]) / (total_count - mid)
        delta = round(second_half_avg - first_half_avg, 1)

        if delta >= 0.8:
            trajectory_text = f"Rising Stamina (+{delta} pts) — Progressive Energy Recovery"
            trajectory_dir = "Rising"
        elif delta <= -0.8:
            trajectory_text = f"Declining Stamina ({delta} pts) — Progressive Energy Depletion"
            trajectory_dir = "Declining"
        else:
            trajectory_text = f"Stable Baseline (Δ {delta:+.1f} pts) — Consistent Energy Maintenance"
            trajectory_dir = "Stable"
    else:
        trajectory_text = "Single-Point Baseline — Insufficient data for slope analysis"
        trajectory_dir = "Neutral"

    # Stability Rating
    if energy_std_dev < 1.1:
        stability_text = "High Emotional Resilience (Low Variance)"
    elif energy_std_dev < 2.2:
        stability_text = "Normal Healthy Fluctuations (Moderate Variance)"
    else:
        stability_text = "Volatile Stamina Swings (High Variance)"

    # 4. Activity Impact Analysis (Energy Boosters vs Drains)
    activity_impacts = []
    booster_acts = []
    drain_acts = []

    for act, e_list in activity_energy.items():
        act_avg = round(sum(e_list) / len(e_list), 1)
        diff = round(act_avg - avg_energy, 1)
        act_top_mood = max(set(activity_moods[act]), key=activity_moods[act].count)
        
        impact_entry = {
            "activity": act,
            "count": len(e_list),
            "avg_energy": act_avg,
            "energy_delta": diff,
            "dominant_mood": act_top_mood,
            "dominant_mood_emoji": MOOD_MAP.get(act_top_mood, {}).get("emoji", "✨")
        }
        activity_impacts.append(impact_entry)

        if diff >= 0.3:
            booster_acts.append((act, act_avg, diff))
        elif diff <= -0.5:
            drain_acts.append((act, act_avg, diff))

    activity_impacts.sort(key=lambda x: x["avg_energy"], reverse=True)

    # 5. Burnout Risk Index
    negative_moods_count = mood_counts.get("Tired", 0) + mood_counts.get("Stressed", 0) + mood_counts.get("Sad", 0)
    burnout_ratio = round((negative_moods_count / total_count) * 100, 1)

    if burnout_ratio <= 15:
        burnout_level = "LOW RISK (Healthy Capacities)"
        burnout_color = "#10b981"
    elif burnout_ratio <= 35:
        burnout_level = "MILD RISK (Standard Work/Study Load)"
        burnout_color = "#0284c7"
    elif burnout_ratio <= 55:
        burnout_level = "MODERATE RISK (Periodic Fatigue Clusters)"
        burnout_color = "#f59e0b"
    else:
        burnout_level = "ELEVATED RISK (High Exhaustion Potential)"
        burnout_color = "#ef4444"

    # 6. Synthesize the Teacher's Formal Conclusion (Executive Paragraph)
    # This directly answers what the app concludes from the logs!
    conclusion_sentences = []

    # Sentence 1: Period Overview & Baseline
    period_name = "weekly" if period == "weekly" else ("monthly" if period == "monthly" else "cartridge")
    conclusion_sentences.append(
        f"Over this {period_name} observation cycle ({start_date.strftime('%b %d')} to {end_date.strftime('%b %d, %Y')}), "
        f"a total of {total_count} journal logs were evaluated, reflecting an overall Wellness Index of {wellness_score}/100 "
        f"and an average stamina level of {avg_energy}/10."
    )

    # Sentence 2: Emotional & Stamina Dynamics
    positive_moods_count = mood_counts.get("Happy", 0) + mood_counts.get("Calm", 0) + mood_counts.get("Good", 0)
    pos_ratio = int(round((positive_moods_count / total_count) * 100))

    if pos_ratio >= 60:
        conclusion_sentences.append(
            f"The psychological baseline is anchored firmly in positive states ({pos_ratio}% of entries were Happy, Calm, or Good), "
            f"with '{top_mood}' {top_mood_emoji} prevailing as the most frequent emotional posture."
        )
    elif pos_ratio >= 40:
        conclusion_sentences.append(
            f"The emotional spectrum displays a balanced equilibrium ({pos_ratio}% positive valence), with '{top_mood}' {top_mood_emoji} "
            f"representing the dominant sentiment alongside natural daily variances."
        )
    elif burnout_ratio >= 30:
        conclusion_sentences.append(
            f"The emotional state registered concentrated periods of physical fatigue or stress ({burnout_ratio}% of entries), "
            f"suggesting increased cognitive or environmental demands during this timeframe."
        )
    else:
        conclusion_sentences.append(
            f"The emotional spectrum is centered in a steady neutral posture ('{top_mood}' {top_mood_emoji}), reflecting pragmatic focus and calm composure."
        )

    # Sentence 3: Activity & Behavioral Correlation Drivers
    if booster_acts:
        best_act = booster_acts[0]
        conclusion_sentences.append(
            f"Behavioral correlation identifies '{best_act[0]}' as the primary energetic booster, generating an optimal stamina rating of "
            f"{best_act[1]}/10 (+{best_act[2]} above baseline)."
        )
    else:
        conclusion_sentences.append(
            f"Engagement across core routines—predominantly '{top_activity}'—maintained stable energy output without severe depletion."
        )

    if drain_acts:
        worst_act = drain_acts[0]
        conclusion_sentences.append(
            f"Conversely, activities under '{worst_act[0]}' correlated with reduced stamina ({worst_act[1]}/10), indicating an area for paced pacing or recovery."
        )

    # Sentence 4: Final Overarching Clinical/Wellness Verdict
    conclusion_sentences.append(
        f"Final Conclusion: The subject exhibits {verdict_status.lower()}, characterized by {trajectory_text.lower()} "
        f"and {stability_text.lower()}."
    )

    executive_conclusion = " ".join(conclusion_sentences)

    # 7. Actionable Recommendations / Prescriptions
    recommendations = []
    if booster_acts:
        recommendations.append(
            f"Prioritize '{booster_acts[0][0]}' Sessions: Your highest energy and emotional clarity correlate with this activity. Schedule regular 30-45 minute blocks."
        )
    else:
        recommendations.append(
            f"Leverage '{top_activity}' Momentum: This activity represents your core routine; introduce intentional micro-breaks to preserve sustained stamina."
        )

    if burnout_ratio > 30:
        recommendations.append(
            "Implement Restorative Sleep & Decompression: With fatigue markers noted in multiple entries, target 7.5+ hours of sleep and evening screen-free wind-downs."
        )
    else:
        recommendations.append(
            "Maintain Positive Emotional Resilience: Continue existing mindful habits; emotional stability is currently in a strong protective zone."
        )

    if drain_acts:
        recommendations.append(
            f"Pace High-Drain Categories: Break '{drain_acts[0][0]}' sessions into smaller 25-minute intervals (Pomodoro technique) to prevent energy drops."
        )
    else:
        recommendations.append(
            "Balanced Scheduling: Distribute challenging cognitive tasks across morning hours when stamina registers highest."
        )

    recommendations.append(
        "Longitudinal Consistency: Continue logging daily reflections to track stamina waveforms and mood shifts across upcoming evaluation periods."
    )

    return {
        "period": period,
        "period_label": period_label,
        "total_entries": total_count,
        "has_data": True,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "avg_energy": avg_energy,
        "energy_std_dev": round(energy_std_dev, 2),
        "wellness_score": wellness_score,
        "verdict": verdict,
        "verdict_status": verdict_status,
        "verdict_emoji": verdict_emoji,
        "badge_color": badge_color,
        "top_mood": top_mood,
        "top_mood_emoji": top_mood_emoji,
        "top_activity": top_activity,
        "trajectory_text": trajectory_text,
        "trajectory_dir": trajectory_dir,
        "stability_text": stability_text,
        "burnout_level": burnout_level,
        "burnout_ratio": burnout_ratio,
        "burnout_color": burnout_color,
        "executive_conclusion": executive_conclusion,
        "recommendations": recommendations,
        "activity_impacts": activity_impacts,
        "mood_counts": mood_counts,
        "entries": sorted(filtered_entries, key=lambda x: parse_entry_date(x.get("date", "")), reverse=True)
    }


def generate_html_report(report_data, personality_theme=None):
    """
    Constructs a university-grade, high-aesthetic printable HTML report.
    Includes print stylesheet, responsive executive summary cards, and one-click print triggers.
    Fully offline, zero CDN dependencies.
    """
    if personality_theme is None:
        p_name = get_active_personality()
        personality_theme = PERSONALITY_THEMES.get(p_name, PERSONALITY_THEMES["Cyber Gamer"])

    t = personality_theme
    accent = t.get("accent_primary", "#0284c7")
    accent_dark = "#0369a1"
    gold = t.get("accent_gold", "#b45309")
    green = t.get("accent_green", "#15803d")
    now_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Render entries rows
    entries_rows_html = ""
    for e in report_data.get("entries", []):
        m = e.get("mood", "Good")
        emoji = MOOD_MAP.get(m, {}).get("emoji", "😊")
        en = e.get("energy", 5)
        act = e.get("activity", "Other")
        d = e.get("date", "")
        txt = e.get("text", "")
        # Escape HTML
        txt_escaped = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

        entries_rows_html += f"""
        <tr>
            <td style="white-space:nowrap;font-weight:600;color:#1e293b;">{d}</td>
            <td style="white-space:nowrap;"><span class="badge mood-badge">{emoji} {m}</span></td>
            <td style="white-space:nowrap;"><span class="energy-meter">{en}/10</span></td>
            <td style="white-space:nowrap;"><span class="badge act-badge">{act}</span></td>
            <td style="color:#334155;font-size:13px;line-height:1.5;">{txt_escaped}</td>
        </tr>
        """

    # Render activity correlations
    activity_cards_html = ""
    for act in report_data.get("activity_impacts", []):
        d_val = act["energy_delta"]
        delta_str = f"+{d_val}" if d_val > 0 else f"{d_val}"
        delta_color = "#15803d" if d_val > 0 else ("#b45309" if d_val == 0 else "#b91c1c")
        activity_cards_html += f"""
        <div class="act-card">
            <div style="font-weight:700;font-size:14px;color:#0f172a;">{act['activity']}</div>
            <div style="font-size:12px;color:#64748b;margin:4px 0;">{act['count']} logged session(s)</div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
                <span style="font-size:13px;color:#334155;">Avg Stamina: <b>{act['avg_energy']}/10</b></span>
                <span style="font-size:12px;font-weight:700;color:{delta_color};">Δ {delta_str}</span>
            </div>
            <div style="font-size:12px;color:#475569;margin-top:4px;">Mood: {act['dominant_mood_emoji']} {act['dominant_mood']}</div>
        </div>
        """

    # Render recommendations
    recs_html = ""
    for idx, rec in enumerate(report_data.get("recommendations", []), 1):
        recs_html += f"""
        <li style="margin-bottom:8px;padding-left:4px;color:#1e293b;line-height:1.5;">
            <b>{idx}.</b> {rec}
        </li>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>LifeLens Executive Report - {report_data.get('period_label')}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f1f5f9;
            color: #0f172a;
            padding: 24px;
            font-size: 14px;
        }}
        .report-sheet {{
            max-width: 960px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        .brand-title {{
            font-size: 24px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.5px;
        }}
        .brand-subtitle {{
            font-size: 13px;
            color: #64748b;
            font-weight: 500;
            margin-top: 4px;
        }}
        .meta-pill {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 8px 14px;
            border-radius: 8px;
            text-align: right;
            font-size: 12px;
            color: #475569;
        }}
        .section-title {{
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            color: #475569;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        /* Executive Conclusion Box */
        .conclusion-box {{
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border: 2px solid #0284c7;
            border-left-width: 8px;
            border-radius: 10px;
            padding: 22px;
            margin-bottom: 28px;
        }}
        .verdict-badge {{
            display: inline-block;
            background: {report_data.get('badge_color', '#0284c7')};
            color: #ffffff;
            font-weight: 800;
            font-size: 13px;
            padding: 6px 14px;
            border-radius: 20px;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }}
        .conclusion-text {{
            font-size: 15px;
            line-height: 1.65;
            color: #0f172a;
            font-weight: 500;
        }}
        /* Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 28px;
        }}
        .metric-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            text-align: left;
        }}
        .metric-label {{
            font-size: 11px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metric-value {{
            font-size: 22px;
            font-weight: 800;
            color: #0f172a;
            margin: 6px 0 2px 0;
        }}
        .metric-note {{
            font-size: 11px;
            color: #94a3b8;
        }}
        /* Activity Breakdown */
        .act-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
            margin-bottom: 28px;
        }}
        .act-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px;
        }}
        /* Recommendations List */
        .recs-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 28px;
        }}
        .recs-card ol {{
            padding-left: 18px;
        }}
        /* Table */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 28px;
            font-size: 13px;
        }}
        th {{
            background: #f8fafc;
            color: #475569;
            font-weight: 700;
            text-align: left;
            padding: 10px 12px;
            border-bottom: 2px solid #e2e8f0;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: top;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .mood-badge {{
            background: #f1f5f9;
            color: #0f172a;
            border: 1px solid #cbd5e1;
        }}
        .act-badge {{
            background: #e0f2fe;
            color: #0369a1;
            border: 1px solid #bae6fd;
        }}
        .energy-meter {{
            font-family: Consolas, monospace;
            font-weight: 700;
            color: #0f172a;
        }}
        /* Signoff Section */
        .signoff-box {{
            border-top: 2px dashed #cbd5e1;
            padding-top: 24px;
            margin-top: 20px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
        }}
        .signoff-line {{
            margin-top: 45px;
            border-top: 1px solid #94a3b8;
            padding-top: 6px;
            font-size: 12px;
            color: #64748b;
            display: flex;
            justify-content: space-between;
        }}
        /* Floating Action Toolbar (Hidden in Print) */
        .toolbar {{
            position: fixed;
            top: 16px;
            right: 16px;
            background: #0f172a;
            padding: 8px 12px;
            border-radius: 8px;
            display: flex;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            z-index: 1000;
        }}
        .toolbar button {{
            background: #0284c7;
            color: #ffffff;
            border: none;
            padding: 8px 14px;
            font-size: 13px;
            font-weight: 700;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: background 0.15s;
        }}
        .toolbar button:hover {{
            background: #0369a1;
        }}
        .toolbar button.secondary {{
            background: #334155;
        }}
        .toolbar button.secondary:hover {{
            background: #475569;
        }}
        /* Print Stylesheet */
        @media print {{
            body {{
                background: #ffffff;
                padding: 0;
            }}
            .toolbar {{
                display: none !important;
            }}
            .report-sheet {{
                box-shadow: none;
                border: none;
                padding: 0;
                max-width: 100%;
            }}
            .conclusion-box {{
                break-inside: avoid;
            }}
            .signoff-box {{
                break-inside: avoid;
            }}
            table, tr, td, th {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>

    <!-- Floating Print & Action Bar -->
    <div class="toolbar">
        <button onclick="window.print()">
            🖨️ Print Report (Ctrl+P / PDF)
        </button>
        <button class="secondary" onclick="window.close()">
            ✖ Close
        </button>
    </div>

    <!-- Printable Report Document Sheet -->
    <div class="report-sheet">
        <!-- Header -->
        <div class="header">
            <div>
                <div class="brand-title">★ LIFELENS EXECUTIVE JOURNAL REPORT</div>
                <div class="brand-subtitle">Automated Behavioral Analytics, Wellness Synthesis & Clinical Conclusion</div>
            </div>
            <div class="meta-pill">
                <div><b>Period:</b> {report_data.get('period_label')}</div>
                <div><b>Generated:</b> {now_str}</div>
                <div><b>Dataset:</b> {report_data.get('total_entries')} Journal Logs Analyzed</div>
            </div>
        </div>

        <!-- 1. Executive Synthesis & Concluding Evaluation -->
        <div class="section-title">
            <span>📋</span> Executive Evaluation & Algorithmic Conclusion
        </div>
        <div class="conclusion-box">
            <div class="verdict-badge">
                {report_data.get('verdict_emoji', '🌟')} {report_data.get('verdict', 'EVALUATION PENDING')}
            </div>
            <div class="conclusion-text">
                {report_data.get('executive_conclusion', '')}
            </div>
        </div>

        <!-- 2. Core Metrics -->
        <div class="section-title">
            <span>📊</span> Quantitative Performance Indicators
        </div>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Wellness Index</div>
                <div class="metric-value" style="color:#0284c7;">{report_data.get('wellness_score', 0)}<span style="font-size:14px;color:#94a3b8;">/100</span></div>
                <div class="metric-note">Composite Valence & Stamina</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Stamina</div>
                <div class="metric-value" style="color:#15803d;">{report_data.get('avg_energy', 0)}<span style="font-size:14px;color:#94a3b8;">/10</span></div>
                <div class="metric-note">{report_data.get('trajectory_dir', 'Stable')} Trend</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Dominant Emotion</div>
                <div class="metric-value" style="font-size:18px;color:#b45309;">{report_data.get('top_mood_emoji', '✨')} {report_data.get('top_mood', 'Good')}</div>
                <div class="metric-note">Primary Psychological Posture</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Burnout Vulnerability</div>
                <div class="metric-value" style="font-size:15px;color:{report_data.get('burnout_color', '#10b981')};">{report_data.get('burnout_ratio', 0)}%</div>
                <div class="metric-note">{report_data.get('burnout_level', 'LOW RISK')}</div>
            </div>
        </div>

        <!-- 3. Activity Impact Breakdown -->
        <div class="section-title">
            <span>⚡</span> Behavioral & Activity Correlation Analysis
        </div>
        <div class="act-grid">
            {activity_cards_html}
        </div>

        <!-- 4. Actionable Recommendations -->
        <div class="section-title">
            <span>💡</span> Prescriptions & Lifestyle Recommendations
        </div>
        <div class="recs-card">
            <ol style="list-style:none;padding:0;">
                {recs_html}
            </ol>
        </div>

        <!-- 5. Complete Log Records -->
        <div class="section-title">
            <span>📖</span> Evaluated Journal Logs ({report_data.get('total_entries')})
        </div>
        <table>
            <thead>
                <tr>
                    <th style="width:110px;">Date</th>
                    <th style="width:120px;">Mood</th>
                    <th style="width:80px;">Stamina</th>
                    <th style="width:120px;">Category</th>
                    <th>Reflection Excerpt</th>
                </tr>
            </thead>
            <tbody>
                {entries_rows_html}
            </tbody>
        </table>

        <!-- 6. Academic Signoff -->
        <div class="signoff-box">
            <div>
                <div style="font-weight:700;color:#334155;">Evaluator / Professor Sign-off:</div>
                <div class="signoff-line">
                    <span>Signature: _______________________</span>
                    <span>Date: _____________</span>
                </div>
            </div>
            <div>
                <div style="font-weight:700;color:#334155;">Student Verification:</div>
                <div class="signoff-line">
                    <span>Student: _______________________</span>
                    <span>Status: Verified</span>
                </div>
            </div>
        </div>

        <div style="text-align:center;font-size:11px;color:#94a3b8;margin-top:30px;">
            Generated completely offline by LifeLens Personal Journaling System • Python & Tkinter Engine
        </div>
    </div>

</body>
</html>
"""
    return html_content


def generate_plain_text_report(report_data):
    """
    Constructs a clean ASCII / Unicode plain text report,
    ideal for copying to clipboard or saving as a .txt file.
    """
    lines = []
    lines.append("=" * 72)
    lines.append("           ★ LIFELENS EXECUTIVE JOURNAL & WELLNESS REPORT ★")
    lines.append("=" * 72)
    lines.append(f"Period:     {report_data.get('period_label')}")
    lines.append(f"Generated:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Total Logs: {report_data.get('total_entries')} entry/entries evaluated")
    lines.append("-" * 72)
    lines.append("")
    lines.append(">> EXECUTIVE CONCLUSION & VERDICT:")
    lines.append(f"[{report_data.get('verdict_emoji', '')} {report_data.get('verdict', '')}]")
    lines.append(f"Wellness Score: {report_data.get('wellness_score', 0)}/100 | Avg Stamina: {report_data.get('avg_energy', 0)}/10")
    lines.append("")
    lines.append(report_data.get('executive_conclusion', ''))
    lines.append("")
    lines.append("-" * 72)
    lines.append(">> KEY PERFORMANCE INDICATORS:")
    lines.append(f"- Dominant Emotion:      {report_data.get('top_mood_emoji', '')} {report_data.get('top_mood', '')}")
    lines.append(f"- Average Stamina:       {report_data.get('avg_energy', 0)}/10 ({report_data.get('trajectory_text', '')})")
    lines.append(f"- Emotional Stability:   {report_data.get('stability_text', '')}")
    lines.append(f"- Burnout Vulnerability: {report_data.get('burnout_level', '')} ({report_data.get('burnout_ratio', 0)}%)")
    lines.append("")
    lines.append("-" * 72)
    lines.append(">> ACTIONABLE RECOMMENDATIONS:")
    for idx, rec in enumerate(report_data.get("recommendations", []), 1):
        lines.append(f"{idx}. {rec}")
    lines.append("")
    lines.append("-" * 72)
    lines.append(">> LOG DETAIL BREAKDOWN:")
    for e in report_data.get("entries", []):
        d = e.get("date", "")
        m = e.get("mood", "")
        emoji = MOOD_MAP.get(m, {}).get("emoji", "")
        en = e.get("energy", 5)
        act = e.get("activity", "")
        txt = e.get("text", "")
        lines.append(f"• [{d}] {emoji} {m:<8} | Stamina: {en:>2}/10 | {act:<10} | {txt}")
    lines.append("=" * 72)
    lines.append("LifeLens Offline Personal Journal • Generated by Python Architecture")
    lines.append("=" * 72)
    return "\n".join(lines)


def print_report(period="weekly", personality_theme=None):
    """
    Generates printable HTML report, saves to local file, and opens it
    in the default browser where the user can print (Ctrl+P / Save as PDF).
    Returns the file path.
    """
    ensure_reports_dir()
    data = generate_report_data(period=period)
    html_content = generate_html_report(data, personality_theme=personality_theme)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lifelens_{period}_report_{timestamp}.html"
    filepath = os.path.join(REPORTS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Open in system default browser for printing
    try:
        webbrowser.open(f"file://{os.path.abspath(filepath)}")
    except Exception as e:
        print(f"Error opening report in browser: {e}")

    return filepath


def export_report_file(target_path, period="weekly", file_format="html", personality_theme=None):
    """Save report to a specific file path in HTML or TXT format."""
    data = generate_report_data(period=period)
    if file_format.lower() == "txt":
        content = generate_plain_text_report(data)
    else:
        content = generate_html_report(data, personality_theme=personality_theme)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True
