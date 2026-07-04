# Ahamnity 🎙️
### Voice-First Multilingual AI Health Triage Assistant for Rural India

> *From Sanskrit: Aham (I) + Nity (Infinity) — "I am Infinite"*

---

## 🌍 Overview
Ahamnity is a voice-first, multilingual AI health triage assistant designed 
for rural India. A patient speaks their symptoms in Marathi, Hindi, or English 
— Ahamnity transcribes, triages risk level, speaks the result back in their 
language, locates the nearest government hospital, and surfaces applicable 
government health schemes.

No reading ability required. No English required.

---

## 🚨 The Problem
Rural India faces three critical healthcare barriers:
- **Language Gap** — 800M+ Indians speak Hindi/regional languages. 
  Almost all digital health tools are English-only.
- **Awareness Gap** — Most eligible rural households are unaware of 
  schemes like Ayushman Bharat and MJPJAY.
- **Triage Gap** — Rural patients cannot assess whether their condition 
  needs home rest, a PHC visit, or emergency care.

---

## ✅ The Solution — 6-Agent Architecture

| Agent | Function |
|---|---|
| 🎙️ Voice Agent | Transcribes speech — Groq Whisper API |
| 🧠 Triage Agent | Risk classification — OpenRouter LLM |
| 🚨 Red Flag Override | Emergency detection — runs in parallel |
| 📍 Locator Agent | Nearest govt PHC/hospital — Google Maps |
| 📋 Scheme Agent | Government scheme matching — curated JSON |
| 🔔 Follow-up System | 24-hour Low Risk check-in |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Speech-to-Text | Groq Whisper API |
| AI Triage | OpenRouter (LLM) |
| Voice Output | Google Cloud TTS |
| Frontend | React.js |
| Backend | Python + FastAPI |
| Database | Supabase (PostgreSQL) |
| Hospital Locator | Google Maps Places API |
| Deployment | Render |

---

## 👥 ASHA Worker Dashboard
High-risk case alerts pushed in real-time to ASHA workers via 
Supabase. ASHA workers can monitor cases, acknowledge alerts, 
and track follow-up outcomes in their coverage area.

---

## 📌 Project Status
**Week 1** — Architecture, Literature Survey, Documentation ✅  
**Week 2** — Core voice pipeline, MVP development 🔄  
**Week 3** — ASHA layer, full integration, testing 📅  
**Week 4** — Demo, research paper, final submission 📅  

---

## 🏆 TechForGood 2026
IEEE MIT-ADT University Student Branch  
In collaboration with IEEE Maharashtra Section & IEEE Region 10 AIPSCC  
Mentor: Dr. Yogesh Golhar  
Team: Ahamnity | Duration: June 1–30, 2026
