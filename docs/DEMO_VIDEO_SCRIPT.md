# Demo Video Script: 3-Minute Product Walkthrough

This script maps out a 3-minute video showcase of the AURA platform, highlighting key interactive elements to impress hackathon evaluators.

---

## Act 1: The Hook (0:00 - 0:30)
* **Visual on Screen:** Close-up of speaker or high-definition footage of Indian city smog. Cuts to the login screen of AURA and transitions to the main dashboard showing a dark, high-contrast city map with glowing markers.
* **Narration (Voiceover):**
  *"Every winter, Indian metros face a silent emergency. While our cities are filled with air quality monitoring stations, a massive gap remains: only 31% of monitored cities have any active response protocol when air quality hits hazardous levels. Administrations are drowning in data, but starving for action. Today, we present AURA: the Air Quality Urban Response Agent, a smart city intelligence platform that turns passive monitoring into proactive, evidence-based intervention."*
* **Action on Screen:** The user logs in, and the main Map Dashboard loads with smooth transitions.

---

## Act 2: Hyperlocal Forecasting & Attribution (0:30 - 1:15)
* **Visual on Screen:** Screen shifts to the **Map & Forecasting** tab. The cursor moves over the interactive map of Bengaluru, clicking on the *Peenya Industrial Area* ward polygon, which is colored in crimson red (AQI 210).
* **Narration (Voiceover):**
  *"Unlike traditional dashboards that show city-wide averages, AURA operates at the hyperlocal ward level. By clicking on Peenya, we can view its current AQI and its 72-hour forecast, powered by our hybrid XGBoost-LSTM engine. Notice the confidence intervals, mapping potential pollution levels based on wind speed and direction."*
* **Action on Screen:** Show the cursor hovering over the forecast chart, highlighting points along the 24, 48, and 72-hour markers. The camera zooms into the **Source Attribution** widget.
* **Narration (Voiceover):**
  *"But knowing the forecast isn't enough; we need to know who is responsible. Our Source Attribution Agent runs spatial regression analysis against nearby traffic, factory permits, and satellite thermal data, showing that industrial emissions are currently contributing 42% of Peenya’s particulate load."*

---

## Act 3: Enforcement Intelligence in Action (1:15 - 1:45)
* **Visual on Screen:** Click on the **Enforcement Intelligence** tab. The interface transitions to a prioritized list of hotspots.
* **Narration (Voiceover):**
  *"AURA's Enforcement Agent helps prioritize municipal response by ranking hotspots using a combination of forecast severity and nearby receptors like schools and hospitals. We can review a case file, inspect the satellite-detected anomalies, and dispatch inspectors with one click."*
* **Action on Screen:** Click on the first case in the list, revealing details. The user clicks `Dispatch Inspector`, showing a confirmation popup: *"Dispatch alert sent to Officer R. K. Sharma."*

---

## Act 4: The What-If Simulator & Public Safety (1:45 - 2:40)
* **Visual on Screen:** Transition to the **Policy Simulator** tab. The cursor adjusts the traffic slider to -30% and toggles the Construction Halt switch.
* **Narration (Voiceover):**
  *"AURA also serves as a policy playground. In our What-If Simulator, administrators can model interventions before deploying them. If we reduce traffic congestion by 30% and pause construction, our dispersion algorithms forecast the exact AQI reduction across all wards, alongside estimated carbon offsets."*
* **Action on Screen:** The bar graphs recalculate dynamically, showing wards dropping from red to orange/yellow. The cursor shifts to the **Citizen Advisory** panel, selects "Asthmatics" and switches the language from English to Kannada.
* **Narration (Voiceover):**
  *"To protect citizens, AURA automatically pushes localized health advisories. Here we see an asthmatic advisory generated and translated into Kannada, ready to be sent to WhatsApp groups and public transit displays."*

---

## Act 5: AI Copilot & Wrap-up (2:40 - 3:00)
* **Visual on Screen:** The user navigates to the **AI Copilot** chat panel, clicks the quick-query button: *"Why is AQI increasing in Zone 4?"* and watches the typing effect output a detailed explanation.
* **Narration (Voiceover):**
  *"Finally, our AI Copilot allows administrators to query data in natural language, acting as an environmental advisor on demand. AURA is a scalable, containerized, smart city platform ready to help cities breathe easier. Thank you."*
* **Visual on Screen:** Fade to black showing GitHub repo details and the project team names.
