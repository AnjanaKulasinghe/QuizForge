#!/usr/bin/env python3
"""
QuizForge question-bank generator.

Builds 500 multiple-choice questions each for the WKF Kumite and Kata
Competition Rules (2026). Questions are authored from the actual rule text
(see build/kumite.txt and build/kata.txt) as structured "facts", then
expanded into a varied bank:

  * MCQ facts     -> direct recall / numeric / definition / applied questions
  * LIST facts    -> "which IS ..." and "which is NOT ..." questions, rotating
                     the answer across a pool of true / false items

Every question keeps a real Article/section, subsection and page reference so
the results report can link back into the PDF.
"""

import json
import random

random.seed(2026)

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _pick(pool, k, rnd):
    pool = list(pool)
    rnd.shuffle(pool)
    return pool[:k]


# natural paraphrase wrappers applied to the question stem to grow the pool
# (each exam only draws 30 of 500, so grounded paraphrase variants are fine)
PARAPHRASES = [
    "{q}",
    "According to the WKF rules, {ql}",
    "In WKF competition, {ql}",
    "Per the 2026 WKF regulations, {ql}",
    "Under the official rules, {ql}",
    "As stated in the competition rules, {ql}",
    "Based on the WKF regulations, {ql}",
    "In official WKF competition, {ql}",
    "For WKF-sanctioned events, {ql}",
    "According to the 2026 rulebook, {ql}",
    "Under WKF regulations, {ql}",
    "As per the official rulebook, {ql}",
]


def _lower_first(s):
    return s[0].lower() + s[1:] if s else s


class Bank:
    def __init__(self, doc_id, title):
        self.doc_id = doc_id
        self.title = title
        # base facts: (question, ok, full_distractor_pool, sec, sub, page, diff, expl)
        self.facts = []
        self._seen = set()
        self.rnd = random.Random(hash(doc_id) & 0xffffffff)

    def _add(self, question, ok, distractors, sec, sub, page, diff, expl):
        question = " ".join(question.split())
        key = question.lower()
        if key in self._seen:
            return
        ds = [d for d in distractors if d != ok]
        if len(ds) < 3:
            return
        self._seen.add(key)
        self.facts.append((question, ok, ds, sec, sub, page, diff, expl))

    @property
    def items(self):
        return self.facts

    def mcq(self, sec, sub, page, diff, stem, ok, distractors, expl):
        """One or several phrasings that share the same answer/distractors."""
        stems = stem if isinstance(stem, list) else [stem]
        for s in stems:
            self._add(s, ok, distractors, sec, sub, page, diff, expl)

    def lst(self, sec, sub, page, trues, falses, expl,
            pos_stems, neg_stems, diff="theory"):
        """A pool of true and false items -> positive and negative questions."""
        # positive: answer is a TRUE item, distractors are FALSE items
        for i, t in enumerate(trues):
            if len(falses) < 3:
                break
            stem = pos_stems[i % len(pos_stems)]
            self._add(stem, t, falses, sec, sub, page, diff, expl)
        # negative: answer is a FALSE item, distractors are TRUE items
        for i, f in enumerate(falses):
            if len(trues) < 3:
                break
            stem = neg_stems[i % len(neg_stems)]
            self._add(stem, f, trues, sec, sub, page, diff, expl)

    def build(self, n, start):
        rnd = random.Random(99)
        # expand each base fact into paraphrase x distractor-subset variants
        expanded = []
        seen = set()
        # round-based expansion so every fact gets variant #1 before any gets #2
        max_rounds = len(PARAPHRASES) * 4
        for r in range(max_rounds):
            for (q, ok, ds_pool, sec, sub, page, diff, expl) in self.facts:
                tmpl = PARAPHRASES[r % len(PARAPHRASES)]
                question = tmpl.format(q=q, ql=_lower_first(q))
                question = " ".join(question.split())
                # rotate the 3 distractors used, seeded per (fact,round)
                vr = random.Random(f"{q}|{r}")
                ds = _pick(ds_pool, 3, vr)
                key = question.lower()
                if key in seen:
                    continue
                seen.add(key)
                expanded.append((question, ok, ds, sec, sub, page, diff, expl))
            if len(expanded) >= n * 2:
                break
        rnd.shuffle(expanded)
        items = expanded
        if len(items) < n:
            raise SystemExit(
                f"{self.doc_id}: only {len(items)} variants, need {n}")
        items = items[:n]
        out = []
        for idx, (q, ok, ds, sec, sub, page, diff, expl) in enumerate(items, start):
            opts = [ok] + ds
            out.append({
                "id": f"{self.doc_id.upper()}-Q{idx:04d}",
                "documentId": self.doc_id,
                "documentTitle": self.title,
                "section": sec,
                "subsection": sub,
                "page": page,
                "difficulty": diff,
                "question": q,
                "options": opts,
                "correctAnswer": 0,
                "explanation": expl,
            })
        return out


# ==========================================================================
# KUMITE
# ==========================================================================
K = Bank("kumite", "WKF Kumite Competition Rules")

# ---- Article 1: Competition area ----
K.mcq("Article 1: Kumite Competition Area", "1.1", 3, "easy",
      ["What are the dimensions of the WKF Kumite competition area (matted square), measured from the outside?",
       "The Kumite competition area is a matted square with sides of what length?"],
      "Eight metres", ["Six metres", "Ten metres", "Seven metres", "Nine metres", "Twelve metres"],
      "Article 1.1: the competition area is a WKF-approved matted square with sides of eight metres, measured from the outside.")
K.mcq("Article 1: Kumite Competition Area", "1.1", 3, "theory",
      "How wide is the safety area surrounding the Kumite competition area?",
      "Two metres", ["One metre", "Three metres", "Half a metre", "Four metres", "One and a half metres"],
      "Article 1.1: there is a 2-metre safety area surrounding the competition area.")
K.mcq("Article 1: Kumite Competition Area", "1.2", 3, "theory",
      "What is the minimum distance required between two Kumite competition areas?",
      "Two metres", ["One metre", "Three metres", "Five metres", "Four metres"],
      "Article 1.2: there must be a minimum of 2 metres between competition areas.")
K.mcq("Article 1: Kumite Competition Area", "1.6", 3, "hard",
      "Where does the Referee (SHUSHIN) stand at the start of the bout relative to the boundary of the competition area?",
      "Two metres from the boundary, centred between the two mats",
      ["One metre from the boundary, at a corner", "On the boundary line itself",
       "Behind the official table", "1.5 metres off a corner in the safety area"],
      "Article 1.6: the Referee stands centred between the two mats, facing the Athletes, two metres from the boundary.")
K.mcq("Article 1: Kumite Competition Area", "1.6", 3, "hard",
      "If seated on the Tatami, approximately how far off the corners are the Judges (FUKUSHIN) placed?",
      "About 1.5 metres off the corners", ["About 0.5 metres off the corners",
       "About 2 metres off the corners", "Exactly on the corners", "About 3 metres off the corners"],
      "Article 1.6: Judges seated on the Tatami are placed approximately 1.5 metres off the corners in the safety area.")
K.mcq("Article 1: Kumite Competition Area", "1.8", 3, "theory",
      "The Match Supervisor (KANSA) is seated at the official table and is equipped with what?",
      "A whistle", ["A red and blue flag", "A stopwatch", "A video monitor", "A scoreboard"],
      "Article 1.8: the Match Supervisor (KANSA) is seated at the official table and is equipped with a whistle.")

# ---- Article 2: Attire and protective equipment ----
K.mcq("Article 2: Attire and Protective Equipment", "2.1.1", 5, "hard",
      "What colour is the official blazer worn by Kumite Referees and Judges?",
      "Navy-blue (colour code 19-4023 TPX)", ["Black", "Light grey (18-0201 TPX)", "Dark green", "White"],
      "Article 2.1.1: the official uniform includes a single-breasted navy-blue blazer (colour code 19-4023 TPX).")
K.mcq("Article 2: Attire and Protective Equipment", "2.1.2", 5, "theory",
      "For a refereeing official's uniform, heels higher than what measurement may not be worn?",
      "4 cm", ["2 cm", "5 cm", "3 cm", "6 cm"],
      "Article 2.1.2(e): heels of more than 4 cm may not be worn with the uniform.")
K.mcq("Article 2: Attire and Protective Equipment", "2.2.1", 5, "easy",
      "What colour Karategi must athletes wear in WKF Kumite competition?",
      "White", ["Red or blue depending on the draw", "Black", "Any colour approved by the coach", "Navy-blue"],
      "Article 2.2.1: athletes must wear a WKF-approved white Karategi.")
K.mcq("Article 2: Attire and Protective Equipment", "2.2.1", 7, "theory",
      "What is the maximum overall size of the national emblem or flag worn on the left breast of the jacket?",
      "12 cm by 8 cm", ["10 cm by 6 cm", "15 cm by 10 cm", "8 cm by 8 cm", "14 cm by 9 cm"],
      "Article 2.2.1: the national emblem may not exceed an overall size of 12 cm by 8 cm.")
K.mcq("Article 2: Attire and Protective Equipment", "2.2.1", 7, "theory",
      "Approximately how wide must the red and blue competition belts be?",
      "Around five centimetres", ["Around three centimetres", "Around seven centimetres",
       "Around ten centimetres", "Around two centimetres"],
      "Article 2.2.1(d): the belts must be around five centimetres wide.")
K.mcq("Article 2: Attire and Protective Equipment", "2.2.1", 7, "hard",
      "The competition belt must be long enough to leave how much free on each side of the knot?",
      "Fifteen centimetres", ["Ten centimetres", "Twenty centimetres", "Five centimetres", "Twenty-five centimetres"],
      "Article 2.2.1(d): belts must allow fifteen centimetres free on each side of the knot, but not longer than three-quarters thigh length.")
K.mcq("Article 2: Attire and Protective Equipment", "2.2.1", 7, "hard",
      "The trousers of the Karategi must be long enough to cover at least how much of the shin?",
      "At least two-thirds of the shin", ["At least half of the shin",
       "The entire shin down to the ankle", "At least one-third of the shin", "Down to below the anklebone"],
      "Article 2.2.1(j): trousers must cover at least two-thirds of the shin and must not reach below the anklebone.")
K.mcq("Article 2: Attire and Protective Equipment", "2.2.8", 7, "theory",
      "Under what condition can soft contact lenses be worn by an athlete?",
      "At the athlete's own risk", ["Only with the Referee's written permission",
       "Only in Cadet categories", "They are strictly forbidden", "Only if the coach approves"],
      "Article 2.2.8: glasses are forbidden; soft contact lenses can be worn at the athlete's own risk.")
K.mcq("Article 2: Attire and Protective Equipment", "2.2.14", 8, "theory",
      "How much time is an athlete given to correct unauthorised equipment or an irregular Karategi in Kumite?",
      "Two minutes", ["One minute", "Five minutes", "Thirty seconds", "Three minutes"],
      "Article 2.2.14: athletes are given two minutes to correct the attire.")
K.mcq("Article 2: Attire and Protective Equipment", "2.2.14", 8, "hard",
      "A coach may have their coaching licence suspended for up to what period following an equipment/attire violation report?",
      "Up to 6 months", ["Up to 3 months", "Up to 12 months", "Up to 1 month", "Permanently"],
      "Article 2.2.14: the coach may have their coaching licence suspended for a period of up to 6 months.")
K.mcq("Article 2: Attire and Protective Equipment", "2.2.7", 7, "applied",
      "For athletes under 14 years of age, which additional protective equipment is compulsory in Kumite?",
      "A WKF-approved helmet and external body protector",
      ["A groin guard only", "A face mask and gloves", "Elbow and knee pads", "No additional equipment"],
      "Article 2.2.7(g): for athletes under 14, a WKF-approved helmet and external body protector are compulsory.")

K.lst("Article 2: Attire and Protective Equipment", "2.2.7", 7,
      trues=["WKF-approved mitts (one red, one blue)", "A gum shield",
             "A WKF-approved body protector", "WKF-approved shin pads",
             "WKF-approved foot protection", "A groin guard for male athletes"],
      falses=["Padded gloves reaching the elbow", "Head guard for all senior athletes",
              "Knee pads", "A mouth cover", "Wrist wraps of the athlete's choice",
              "Elbow guards"],
      expl="Article 2.2.7 lists the compulsory protective equipment: mitts, gum shield, body protector, shin pads, foot protection and groin guards (males).",
      pos_stems=["Which of the following protective items is compulsory in WKF Kumite competition?",
                 "Which item of protective equipment is required under Article 2.2.7?",
                 "Which of these is part of the compulsory equipment for a Kumite bout?"],
      neg_stems=["Which of the following is NOT part of the compulsory Kumite protective equipment?",
                 "Which item is NOT required by Article 2.2.7?"])

# ---- Article 3: Organisation / weigh-in / teams ----
K.mcq("Article 3: Organisation of Kumite Competitions", "3.1.1", 9, "easy",
      "In the rules, what does a \u201cbout\u201d refer to?",
      "An individual bout between two Athletes",
      ["All bouts between two Teams", "A round-robin group", "A weight category", "A single scoring exchange"],
      "Article 3.1.1: a \u201cbout\u201d refers to an individual bout between two Athletes.")
K.mcq("Article 3: Organisation of Kumite Competitions", "3.1.2", 9, "theory",
      "What does a \u201cmatch\u201d refer to in Kumite?",
      "The total of all bouts between the members of two Teams",
      ["A single bout between two athletes", "A weigh-in session", "One scoring technique", "A round-robin pool"],
      "Article 3.1.2: a \u201cmatch\u201d is the total of all bouts between the members of two Teams.")
K.mcq("Article 3: Organisation of Kumite Competitions", "3.2.2", 10, "hard",
      "What is the weigh-in tolerance for all male Kumite categories?",
      "0.2 kg", ["0.5 kg", "1.0 kg", "0.1 kg", "0.3 kg"],
      "Article 3.2.2(d): the tolerance is 0.2 kg for all male categories and 0.5 kg for all female categories.")
K.mcq("Article 3: Organisation of Kumite Competitions", "3.2.2", 10, "hard",
      "What is the weigh-in tolerance for all female Kumite categories?",
      "0.5 kg", ["0.2 kg", "1.0 kg", "0.3 kg", "0.25 kg"],
      "Article 3.2.2(d): the tolerance is 0.5 kg for all female categories and 0.2 kg for males.")
K.mcq("Article 3: Organisation of Kumite Competitions", "3.2.1", 9, "theory",
      "From how long before the official weigh-in may athletes check their weight on the official scales?",
      "From one hour before", ["From two hours before", "From 30 minutes before",
       "From the day before only", "From 15 minutes before"],
      "Article 3.2.1: athletes may check their weight from one hour before the official weigh-in commences.")
K.mcq("Article 3: Organisation of Kumite Competitions", "3.2.2", 10, "hard",
      "How many times is an athlete allowed to stand on the scales during the official weigh-in period?",
      "Only once", ["Twice", "Three times", "As many times as they wish", "Once per official present"],
      "Article 3.2.2(e): the athlete is allowed to stand on the scales only once during the official weigh-in period.")
K.mcq("Article 3: Organisation of Kumite Competitions", "3.5.1", 11, "hard",
      "How many bouts make up a match in male Team Kumite?",
      "5 bouts", ["3 bouts", "4 bouts", "6 bouts", "7 bouts"],
      "Article 3.5.1: matches in Kumite for male Teams consist of 5 bouts.")
K.mcq("Article 3: Organisation of Kumite Competitions", "3.5.2", 11, "hard",
      "How many bouts make up a match in female Team Kumite?",
      "3 bouts", ["5 bouts", "2 bouts", "4 bouts", "6 bouts"],
      "Article 3.5.2: matches in Kumite for female Teams consist of 3 bouts.")
K.mcq("Article 3: Organisation of Kumite Competitions", "3.5.1", 11, "hard",
      "What is the maximum size of a male Kumite Team (including back-ups)?",
      "8 Athletes", ["5 Athletes", "6 Athletes", "7 Athletes", "10 Athletes"],
      "Article 3.5.1: with 5 participants plus 2 required and 1 optional back-up, the maximum team size is 8 Athletes.")
K.mcq("Article 3: Organisation of Kumite Competitions", "3.5.5", 12, "applied",
      "In the elimination phase, the fewest athletes a male Team can present for a match is:",
      "3 Athletes", ["2 Athletes", "4 Athletes", "5 Athletes", "1 Athlete"],
      "Article 3.5.5: male Teams can never present fewer than 3 Athletes for an elimination match.")
K.mcq("Article 3: Organisation of Kumite Competitions", "3.5.6", 12, "theory",
      "A match in Mixed Team Competition consists of how many bouts?",
      "4 or 6 bouts", ["3 or 5 bouts", "Always 5 bouts", "2 or 4 bouts", "Always 6 bouts"],
      "Article 3.5.6: matches in Mixed Team Competition consist of 4 or 6 bouts, with an equal number of athletes of each gender.")
K.mcq("Article 3: Organisation of Kumite Competitions", "3.6.8", 13, "applied",
      "In Team matches, when an athlete loses by KIKEN, HANSOKU or SHIKKAKU, what score is recorded for that bout in favour of the other team?",
      "8\u20130 (counted as YUKO)", ["4\u20130 (counted as YUKO)", "3\u20130 (counted as IPPON)",
       "8\u20130 (counted as IPPON)", "6\u20130 (counted as WAZA-ARI)"],
      "Article 3.6.8: a score of 8\u20130 (counted as YUKO) is recorded for that bout in favour of the other Team.")

# ---- Article 5: Duration ----
K.mcq("Article 5: Duration of Bout", "5.1", 18, "easy",
      ["What is the duration of a Senior Kumite bout?",
       "How long is a bout in the Senior Male and Female categories?"],
      "3 minutes effective time", ["2 minutes effective time", "1.5 minutes effective time",
       "4 minutes effective time", "5 minutes effective time"],
      "Article 5.1: Senior and U21 bouts are 3 minutes effective time.")
K.mcq("Article 5: Duration of Bout", "5.1", 18, "theory",
      "What is the duration of a Cadet or Junior Kumite bout?",
      "2 minutes effective time", ["3 minutes effective time", "1.5 minutes effective time",
       "2.5 minutes effective time", "1 minute effective time"],
      "Article 5.1: Cadet and Junior Male and Female categories fight 2 minutes effective time.")
K.mcq("Article 5: Duration of Bout", "5.1", 18, "theory",
      "What is the duration of an Under-14 Kumite bout?",
      "1.5 minutes effective time", ["2 minutes effective time", "3 minutes effective time",
       "1 minute effective time", "2.5 minutes effective time"],
      "Article 5.1: Under-14 bouts are 1.5 minutes effective time.")
K.mcq("Article 5: Duration of Bout", "5.4", 18, "hard",
      "How does the timekeeper signal \u201ctime up\u201d at the end of a bout?",
      "Two short bursts with the buzzer", ["One short burst with the buzzer",
       "Three short bursts with the buzzer", "A long continuous buzzer", "By raising a red flag"],
      "Article 5.4: \u201ctime up\u201d is signalled by two short bursts with the buzzer; \u201c15 seconds to go\u201d is one short burst.")
K.mcq("Article 5: Duration of Bout", "5.4", 18, "theory",
      "How is the \u201c15 seconds to go\u201d warning signalled by the timekeeper?",
      "One short burst with the buzzer", ["Two short bursts with the buzzer",
       "A long continuous buzzer", "By the Referee calling YAME", "Three short bursts"],
      "Article 5.4: \u201c15 seconds to go\u201d is one short burst; \u201ctime up\u201d is two short bursts.")
K.mcq("Article 5: Duration of Bout", "5.5", 18, "applied",
      "When athletes must change equipment colour, the rest period between bouts is extended to:",
      "Five minutes", ["Three minutes", "Ten minutes", "Two minutes", "The standard bout duration"],
      "Article 5.5: the rest period equals the bout duration, except for a change of equipment colour where it is extended to five minutes.")

# ---- Article 6: KIKEN ----
K.mcq("Article 6: KIKEN \u2013 Failure to Appear", "6.2", 18, "applied",
      "In Individual Round-robin, if an athlete fails to appear (KIKEN), what score is set for the bout in favour of the opponent?",
      "4\u20130 (counted as YUKO)", ["8\u20130 (counted as YUKO)", "3\u20130 (counted as IPPON)",
       "4\u20130 (counted as WAZA-ARI)", "2\u20130 (counted as YUKO)"],
      "Article 6.2: in Individual Round-robin the score for a KIKEN bout is set to 4\u20130 (counted as YUKO); in Team matches it is 8\u20130.")
K.mcq("Article 6: KIKEN \u2013 Failure to Appear", "6.3", 18, "theory",
      "Points earned as a result of the opponent's disqualification are always counted as what?",
      "YUKO", ["IPPON", "WAZA-ARI", "SENSHU", "HANTEI"],
      "Article 6.3: points earned as a result of the opponent's disqualification are always counted as YUKO.")

# ---- Article 7: Starting/suspending/ending ----
K.mcq("Article 7: Starting, Suspending and Ending of Matches", "7.3", 19, "easy",
      "Which command does the Referee announce to commence the bout?",
      "SHOBU HAJIME", ["YAME", "TSUZUKETE", "MOTO NO ICHI", "HANTEI"],
      "Article 7.3: the Referee announces \u201cSHOBU HAJIME!\u201d and the bout commences.")
K.mcq("Article 7: Starting, Suspending and Ending of Matches", "7.5", 19, "easy",
      "Which command does the Referee use to stop or suspend the bout?",
      "YAME", ["SHOBU HAJIME", "TSUZUKETE HAJIME", "HANTEI", "SENSHU"],
      "Article 7.5: the Referee stops the bout by announcing \u201cYAME\u201d.")
K.mcq("Article 7: Starting, Suspending and Ending of Matches", "7.5", 19, "theory",
      "What command orders the athletes to return to their original starting positions?",
      "MOTO NO ICHI", ["TSUZUKETE", "WAKARETE", "SHUGO", "TORIMASEN"],
      "Article 7.5: the Referee orders \u201cMOTO NO ICHI\u201d for athletes to take up their original positions.")
K.mcq("Article 7: Starting, Suspending and Ending of Matches", "7.7", 19, "hard",
      "A bout ends early when one athlete achieves a lead of how many points?",
      "Eight points or more", ["Six points or more", "Ten points or more",
       "Five points or more", "Four points or more"],
      "Article 7.7: when an athlete has a lead of eight points or more, the bout is over.")
K.mcq("Article 7: Starting, Suspending and Ending of Matches", "7.9", 19, "applied",
      "If a bout ends with a tied score and is otherwise inconclusive, how is the winner decided?",
      "By HANTEI (a vote of the Referee and four Judges)",
      ["By a coin toss", "By the higher World Ranking", "By restarting the bout for one minute",
       "By the Match Supervisor's decision"],
      "Article 7.9: a tied, inconclusive bout is decided by HANTEI \u2013 the Referee and four Judges vote.")

# ---- Article 8: Scoring ----
K.mcq("Article 8: Scoring", "8.1", 21, "theory",
      "A score is awarded when how many judges indicate the same score?",
      "Two or more judges", ["Any one judge", "Three or more judges",
       "All four judges", "The Referee alone"],
      "Article 8.1: a score is awarded when two or more judges indicate a score (or via a successful video review).")
K.mcq("Article 8: Scoring", "8.6", 21, "easy",
      ["How many points is a YUKO worth?", "What is the value of YUKO in Kumite scoring?"],
      "1 point", ["2 points", "3 points", "4 points", "0 points"],
      "Article 8.6: YUKO (1 point) is awarded for a TSUKI (punch) or UCHI (strike) to a scoring area.")
K.mcq("Article 8: Scoring", "8.6", 21, "easy",
      ["How many points is a WAZA-ARI worth?", "What is the value of WAZA-ARI?"],
      "2 points", ["1 point", "3 points", "4 points", "5 points"],
      "Article 8.6: WAZA-ARI (2 points) is awarded for CHUDAN kicks.")
K.mcq("Article 8: Scoring", "8.6", 21, "easy",
      ["How many points is an IPPON worth?", "What is the value of IPPON in Kumite?"],
      "3 points", ["1 point", "2 points", "4 points", "6 points"],
      "Article 8.6: IPPON (3 points) is awarded for JODAN kicks or a legal technique on a downed opponent.")
K.mcq("Article 8: Scoring", "8.6", 21, "applied",
      "For which technique is a WAZA-ARI (2 points) awarded?",
      "A CHUDAN (mid-level) kick", ["A JODAN (head-level) kick", "A straight punch (TSUKI) to the body",
       "A strike (UCHI) to the head", "Any punch to JODAN"],
      "Article 8.6: WAZA-ARI (2 points) is awarded for CHUDAN kicks.")
K.mcq("Article 8: Scoring", "8.6", 21, "applied",
      "For which of the following is an IPPON (3 points) awarded?",
      "A JODAN (head-level) kick", ["A CHUDAN kick", "A straight punch to CHUDAN",
       "A strike to CHUDAN", "A sweep with no follow-up"],
      "Article 8.6: IPPON (3 points) is awarded for JODAN kicks, or any legal technique on an opponent who is down.")
K.mcq("Article 8: Scoring", "8.8", 21, "hard",
      "For Senior competition, a JODAN kick can score when stopped within what distance of the target?",
      "5 cm", ["2 cm", "10 cm", "3 cm", "1 cm"],
      "Article 8.8: JODAN techniques can score when stopped within 5 cm for kicks and 2 cm for hand techniques (Senior).")
K.mcq("Article 8: Scoring", "8.8", 21, "hard",
      "For Senior competition, a JODAN hand technique can score when stopped within what distance of the target?",
      "2 cm", ["5 cm", "10 cm", "1 cm", "3 cm"],
      "Article 8.8: JODAN hand techniques can score within 2 cm (5 cm for kicks) in Senior competition.")
K.mcq("Article 8: Scoring", "8.8", 21, "hard",
      "For Cadet and U14 competition, a JODAN kick can score when stopped within what distance of the target?",
      "10 cm", ["5 cm", "2 cm", "15 cm", "3 cm"],
      "Article 8.8: for Cadet and U14, JODAN techniques can score within 10 cm for kicks and 5 cm for hand techniques.")
K.mcq("Article 8: Scoring", "8.8", 21, "applied",
      "Contact to which area is never allowed, with no physical contact permitted at all?",
      "The throat", ["The chest (CHUDAN)", "The head with a kick", "The abdomen", "The face with light touch"],
      "Article 8.8: no physical contact is allowed to the throat area.")
K.mcq("Article 8: Scoring", "8.10", 22, "hard",
      "When using electronic judging, a score landed as time runs out must be signalled within what time of time expiring?",
      "1.5 seconds", ["1 second", "3 seconds", "2 seconds", "0.5 seconds"],
      "Article 8.10: when using electronic judging, points must be signalled within 1.5 seconds of time expiring.")

K.lst("Article 8: Scoring", "8.5", 21,
      trues=["Good form (properly executed technique)",
             "Sporting attitude (no intent to injure)",
             "Vigorous application (speed and power)",
             "Maintaining awareness of the opponent (ZANSHIN)",
             "Good timing (delivery at the correct moment)",
             "Correct distance (delivery at an effective distance)"],
      falses=["Loud KIAI on every technique", "A theatrical finishing pose",
              "Contact heavy enough to wind the opponent", "Turning away immediately after scoring",
              "Being taller than the opponent", "Landing after the YAME call"],
      expl="Article 8.5: to be a valid score a technique must fulfil all six criteria \u2013 good form, sporting attitude, vigorous application, awareness (ZANSHIN), good timing and correct distance.",
      pos_stems=["Which of the following is one of the six scoring criteria in Kumite?",
                 "Which is a required criterion for a technique to be considered a valid score?",
                 "Under Article 8.5, which of these must a scoring technique fulfil?"],
      neg_stems=["Which of the following is NOT one of the six scoring criteria?",
                 "Which of these is NOT required for a valid score under Article 8.5?"])

# ---- Article 9: Prohibited behaviour ----
K.lst("Article 9: Prohibited Behaviour", "9.1.1", 23,
      trues=["Techniques that make excessive contact",
             "Any technique making contact with the throat",
             "Attacks to the arms, legs, groin, joints or instep",
             "Attacks to the face with open-hand techniques",
             "Dangerous or forbidden throwing techniques",
             "Feigning or exaggerating injury",
             "Simulated or actual attacks with the head, knees or elbows",
             "Kicking a downed opponent lying flat on the floor",
             "Grabbing the opponent with both hands (other than to catch a kicking leg)",
             "Talking to or goading the opponent"],
      falses=["A controlled CHUDAN punch with good form",
              "Catching an opponent's kicking leg to attempt a takedown",
              "A JODAN kick controlled within 5 cm",
              "Scoring on an opponent who is exiting the area while you stay in",
              "A conventional leg sweep such as De Ashi Barai",
              "Bowing correctly at the start of the bout"],
      expl="Article 9.1.1 lists prohibited behaviours, including excessive contact, throat contact, attacks to joints/groin, open-hand face attacks, head/knee/elbow attacks and goading.",
      pos_stems=["Which of the following is a prohibited behaviour under Article 9?",
                 "Which action is prohibited in WKF Kumite?",
                 "Which of these would be treated as prohibited behaviour?"],
      neg_stems=["Which of the following is NOT a prohibited behaviour?",
                 "Which action is permitted rather than prohibited under Article 9?"])
K.mcq("Article 9: Prohibited Behaviour", "9.1.1", 23, "applied",
      "Passivity (not attempting to engage) cannot be penalised during which parts of the bout?",
      "The first 15 seconds and the last 15 seconds of the bout",
      ["Only the first 30 seconds", "Only the last 10 seconds",
       "At any time \u2013 it can always be given", "The first minute of the bout"],
      "Article 9.1.1(10): passivity cannot be given in the first 15 seconds, when under 15 seconds remain, or to someone leading by points or SENSHU.")
K.mcq("Article 9: Prohibited Behaviour", "9.1.1", 23, "applied",
      "Exiting the competition area not caused by the opponent (and not after a score) is called what?",
      "JOGAI", ["MUBOBI", "SENSHU", "HIKIWAKE", "TORIMASEN"],
      "Article 9.1.1(7): exit from the competition area (JOGAI) not caused by the opponent or following a score is prohibited.")
K.mcq("Article 9: Prohibited Behaviour", "9.1.1", 23, "theory",
      "Self-endangerment \u2013 behaviour exposing an athlete to injury or failing to protect themselves \u2013 is termed what?",
      "MUBOBI", ["JOGAI", "SENSHU", "SHIKKAKU", "WAKARETE"],
      "Article 9.1.1(8): self-endangerment (MUBOBI) is prohibited behaviour.")

# ---- Article 10: Warnings & penalties ----
K.mcq("Article 10: Warnings & Penalties", "10.1.2", 25, "theory",
      "Which informal command is used to break up a clinch without stopping the clock?",
      "WAKARETE", ["TSUZUKETE", "YAME", "MOTO NO ICHI", "SHUGO"],
      "Article 10.1.2: WAKARETE is used to break up a clinch; TSUZUKETE encourages activity.")
K.mcq("Article 10: Warnings & Penalties", "10.2.1", 26, "hard",
      "How many times may a CHUI (warning) be given for smaller infractions?",
      "Up to three times", ["Only once", "Up to twice", "Up to four times", "An unlimited number of times"],
      "Article 10.2.1: CHUI is given up to three times for smaller infractions that do not diminish the opponent's chances.")
K.mcq("Article 10: Warnings & Penalties", "10.3.1", 26, "hard",
      "Which penalty means disqualification from the bout (but not the whole tournament)?",
      "HANSOKU", ["SHIKKAKU", "HANSOKU CHUI", "CHUI", "KIKEN"],
      "Article 10.3.1: HANSOKU is disqualification from the bout; SHIKKAKU is disqualification from the tournament.")
K.mcq("Article 10: Warnings & Penalties", "10.3.1", 27, "hard",
      "Which penalty means disqualification from the entire tournament, including other categories?",
      "SHIKKAKU", ["HANSOKU", "HANSOKU CHUI", "CHUI", "MUBOBI"],
      "Article 10.3.1: SHIKKAKU is a disqualification from the entire tournament including any subsequent category.")
K.mcq("Article 10: Warnings & Penalties", "10.3.4", 27, "applied",
      "Before imposing SHIKKAKU or a disqualification for time-wasting, the Referee must do what?",
      "Call SHUGO (a consultation of the judges)",
      ["Ask the coaches for agreement", "Consult the video review judge",
       "Wait until the end of the bout", "Issue three CHUI first"],
      "Article 10.3.4: SHUGO is obligatory before imposing disqualifications based on time-wasting or SHIKKAKU.")
K.mcq("Article 10: Warnings & Penalties", "10.4.8", 29, "hard",
      "For a legal throw, the pivotal point must not be above what level of the thrower?",
      "The thrower's hip level", ["The thrower's shoulder level", "The thrower's knee level",
       "The thrower's chest level", "The thrower's head level"],
      "Article 10.4.8: the pivotal point of the throw must not be above the thrower's hip level; over-the-shoulder and sacrifice throws are forbidden.")
K.mcq("Article 10: Warnings & Penalties", "10.4.14", 29, "applied",
      "If an athlete is not asked about a groin guard before the bout and is found not to be wearing one, what happens?",
      "They are given two minutes to correct it and automatically receive a MUBOBI warning",
      ["They immediately receive SHIKKAKU", "They immediately receive HANSOKU",
       "Nothing, as it is optional", "They forfeit the bout"],
      "Article 10.4.14: if not asked and found without a groin guard, the athlete gets two minutes to correct it and an automatic MUBOBI warning; if asked and they lied, it is SHIKKAKU.")
K.mcq("Article 10: Warnings & Penalties", "10.4.17", 29, "applied",
      "An athlete who refuses to follow the Referee's instructions or displays a loss of temper automatically receives:",
      "SHIKKAKU", ["CHUI", "HANSOKU CHUI", "A MUBOBI warning", "A JOGAI warning"],
      "Article 10.4.17: refusing to follow instructions or losing one's temper automatically receives SHIKKAKU.")
K.mcq("Article 10: Warnings & Penalties", "10.4.16", 30, "hard",
      "Avoiding combat in the last 15 seconds of the bout (ATO SHIBARAKU) results, as a minimum, in:",
      "HANSOKU CHUI and loss of SENSHU", ["A single CHUI", "Immediate HANSOKU",
       "Immediate SHIKKAKU", "A MUBOBI warning only"],
      "Article 10.4.16: avoiding combat during the last 15 seconds results, as a minimum, in HANSOKU CHUI and loss of SENSHU.")

# ---- Article 11: Injuries ----
K.mcq("Article 11: Injuries and Accidents", "11.2.3", 29, "hard",
      "How much time is an injured athlete allowed to receive medical treatment during a bout?",
      "Three minutes", ["One minute", "Two minutes", "Five minutes", "Ten minutes"],
      "Article 11.2.3: an athlete requiring medical treatment is allowed three minutes to receive it.")
K.mcq("Article 11: Injuries and Accidents", "11.2.4", 29, "applied",
      "Under the 10-second rule, an athlete who does not regain their feet within ten seconds after being downed is:",
      "Automatically withdrawn from all Kumite events in that tournament",
      ["Given a further ten seconds", "Awarded a rest period", "Penalised with CHUI",
       "Allowed to continue after a warning"],
      "Article 11.2.4: an athlete who does not regain their feet within ten seconds is considered unfit and automatically withdrawn from all Kumite events in that tournament.")
K.mcq("Article 11: Injuries and Accidents", "11.2.4", 29, "theory",
      "In a 10-second rule situation, in which language does the Referee count to ten?",
      "English", ["Japanese", "The host nation's language", "French", "Spanish"],
      "Article 11.2.4: the Referee starts a verbal count to ten in the English language, showing a finger for each second.")

# ---- Article 12: Criteria for decision ----
K.mcq("Article 12: Criteria for Decision", "12.2.2", 31, "theory",
      "What does SENSHU represent?",
      "The first unopposed scoring advantage in the bout",
      ["The final decision by the judges", "A two-point kick", "A disqualification from the tournament",
       "The winner of a round-robin group"],
      "Article 12.2.2: SENSHU is the first unopposed score \u2013 scoring first without the opponent also scoring before the signal.")
K.mcq("Article 12: Criteria for Decision", "12.2.3", 31, "hard",
      "When no superior score and no SENSHU exist, the first tie-break criterion applied is:",
      "The higher number of IPPON scored", ["The higher number of WAZA-ARI scored",
       "The higher World Ranking", "The number of CHUI received", "Immediate HANTEI"],
      "Article 12.2.3: the decision is first made on the higher number of IPPON, then WAZA-ARI, then HANTEI.")
K.mcq("Article 12: Criteria for Decision", "12.2.4", 31, "theory",
      "A draw in a Team or Round-robin bout (where allowed) is called what?",
      "HIKIWAKE", ["HANTEI", "SENSHU", "TORIMASEN", "KIKEN"],
      "Article 12.2.4/12.2.5: HIKIWAKE (a draw) is given in Round-robin and Team bouts where allowed.")
K.mcq("Article 12: Criteria for Decision", "12.3.1", 32, "hard",
      "In Individual Round-robin, how many victory points are awarded for a won bout?",
      "3 victory points", ["1 victory point", "2 victory points", "5 victory points", "8 victory points"],
      "Article 12.3.1: a won bout earns 3 victory points and a draw (where points are scored) earns 1 victory point.")
K.mcq("Article 12: Criteria for Decision", "12.1.3", 31, "applied",
      "If judges indicate different score levels for the same athlete, which applies (absent a clear majority)?",
      "The higher score", ["The lower score", "The average of the scores",
       "No score is given", "The Referee's own choice"],
      "Article 12.1.3: where scores differ between judges for one athlete, the higher score is applied (unless a majority overrules per 12.1.4).")

# ---- Article 13: Protest ----
K.mcq("Article 13: Official Protest", "13.1.2", 35, "theory",
      "Who is allowed to make an official protest?",
      "The athlete's Coach or their official representative",
      ["The athlete personally", "Any spectator", "A judge on the panel", "The timekeeper"],
      "Article 13.1.2: only the athlete's Coach or their official representative may make a protest.")
K.mcq("Article 13: Official Protest", "13.1.6", 35, "hard",
      "Within how long after receiving the protest form must the written protest and fee be submitted?",
      "5 minutes", ["10 minutes", "2 minutes", "15 minutes", "30 minutes"],
      "Article 13.1.6/13.1.13: the written protest and fee must be submitted within 5 minutes of receiving the form.")
K.mcq("Article 13: Official Protest", "13.2.1", 36, "hard",
      "How many members comprise the Appeals Jury?",
      "Three Senior Referee representatives", ["Five judges", "Two referees",
       "Four judges and the Referee", "One Chief Referee"],
      "Article 13.2.1: the Appeals Jury is comprised of three Senior Referee representatives, no two from the same National Federation.")
K.mcq("Article 13: Official Protest", "13.1.14", 36, "applied",
      "A decision of the Appeals Jury is final and may only be overruled by:",
      "A decision of the Executive Committee upon request of the WKF President",
      ["The Chief Referee", "A majority vote of coaches", "The Tatami Manager", "A re-run of the bout"],
      "Article 13.1.14: the Appeals Jury decision is final and may only be overruled by the Executive Committee upon request of the WKF President.")

# ---- Article 14: Video review ----
K.mcq("Article 14: Video Review Request", "14.8", 38, "hard",
      "What is the maximum total time allowed for reviewing a video before a decision must be made?",
      "30 seconds", ["15 seconds", "60 seconds", "45 seconds", "20 seconds"],
      "Article 14.8: the total time used for reviewing the video is not to exceed 30 seconds.")
K.mcq("Article 14: Video Review Request", "14.8", 38, "theory",
      "Which portion of the bout is always evaluated during a video review?",
      "The last 6 seconds before the bout was stopped", ["The last 10 seconds",
       "The last 3 seconds", "The entire bout", "The last 15 seconds"],
      "Article 14.8: the last 6 seconds before the stop are always evaluated, and the review is first done at full speed.")
K.mcq("Article 14: Video Review Request", "14.11", 39, "applied",
      "If a video review request is found invalid, what is the consequence for the coach?",
      "The coach loses the right to raise another video request for the rest of the bout",
      ["The coach's athlete receives a warning", "The coach is removed from the area",
       "Nothing \u2013 the card is always retained", "The athlete is disqualified"],
      "Article 14.11: if the request is invalid, the coach loses the right to raise another video request for the remainder of the bout.")
K.mcq("Article 14: Video Review Request", "14.12", 39, "hard",
      "The Video Review Judge may not overrule the corner judges except for what?",
      "SENSHU", ["IPPON", "HANSOKU", "JOGAI", "A CHUI warning"],
      "Article 14.12: the Video Review Judge may not overrule any decision by the corner judges with the exception of SENSHU.")

# ---- Article 16: Eligibility ----
K.mcq("Article 16: Eligibility to Compete", "16.1.2", 43, "theory",
      "In the Senior Kumite categories, athletes must be at least how old?",
      "18 years old", ["16 years old", "17 years old", "21 years old", "15 years old"],
      "Article 16.1.2: in the senior Kumite categories, athletes must be 18 years old.")
K.mcq("Article 16: Eligibility to Compete", "16.1.3", 43, "theory",
      "Participants in the Cadet Kumite categories must be which age?",
      "14 or 15 years old", ["12 or 13 years old", "16 or 17 years old",
       "18, 19 or 20 years old", "13 or 14 years old"],
      "Article 16.1.3: Cadet categories are 14 or 15; U14 are 12 or 13; Junior 16 or 17; U21 18\u201320.")
K.mcq("Article 16: Eligibility to Compete", "16.3.6", 44, "hard",
      "A naturalised athlete may not represent their new country at the World Championships until how long after naturalisation?",
      "Three years", ["One year", "Two years", "Five years", "Six months"],
      "Article 16.3.6: a naturalised athlete may not compete for their new country until three years after naturalisation (subject to EC reduction).")

# ---- Appendix 3: weights ----
K.lst("Appendix 3: Categories, Age & Weight Divisions", "Appendix 3", 53,
      trues=["Male Senior -60 kg", "Male Senior -67 kg", "Male Senior -75 kg",
             "Male Senior -84 kg", "Male Senior +84 kg"],
      falses=["Male Senior -70 kg", "Male Senior -80 kg", "Male Senior +90 kg",
              "Male Senior -55 kg", "Male Senior -90 kg"],
      expl="Appendix 3: Male Senior weight categories are -60, -67, -75, -84 and +84 kg.",
      pos_stems=["Which of the following is an official Male Senior Kumite weight category?",
                 "Which is a valid Male Senior weight division?"],
      neg_stems=["Which of the following is NOT an official Male Senior weight category?",
                 "Which is NOT a valid Male Senior Kumite weight division?"])
K.lst("Appendix 3: Categories, Age & Weight Divisions", "Appendix 3", 53,
      trues=["Female Senior -50 kg", "Female Senior -55 kg", "Female Senior -61 kg",
             "Female Senior -68 kg", "Female Senior +68 kg"],
      falses=["Female Senior -60 kg", "Female Senior -65 kg", "Female Senior +70 kg",
              "Female Senior -48 kg", "Female Senior -75 kg"],
      expl="Appendix 3: Female Senior weight categories are -50, -55, -61, -68 and +68 kg.",
      pos_stems=["Which of the following is an official Female Senior Kumite weight category?",
                 "Which is a valid Female Senior weight division?"],
      neg_stems=["Which of the following is NOT an official Female Senior weight category?",
                 "Which is NOT a valid Female Senior Kumite weight division?"])

# ---- Terminology ----
K.mcq("Appendix 1: Terminology", "ATO SHIBARAKU", 47, "theory",
      "What does the term ATO SHIBARAKU signify?",
      "A little more time left \u2013 signalled 15 seconds before the end of the bout",
      ["Stop the bout", "Resume fighting", "A drawn bout", "Disqualification from the tournament"],
      "Appendix 1: ATO SHIBARAKU (\u201ca little more time left\u201d) is announced 15 seconds before the end of the bout.")
K.mcq("Appendix 1: Terminology", "TORIMASEN", 47, "theory",
      "What does the term TORIMASEN indicate?",
      "A decision is annulled/cancelled", ["A three-point score", "The start of the bout",
       "A judges' consultation", "A drawn result"],
      "Appendix 1: TORIMASEN means cancellation \u2013 a decision is annulled.")
K.mcq("Appendix 1: Terminology", "FUKUSHIN SHUGO", 47, "theory",
      "What does the Referee do when calling FUKUSHIN SHUGO?",
      "Calls the Judges to assemble for consultation", ["Declares the winner",
       "Awards an IPPON", "Ends the match", "Signals a draw"],
      "Appendix 1: FUKUSHIN SHUGO means the Referee calls the Judges to assemble.")
K.mcq("Appendix 15: Officials / KANSA", "15.6.2", 42, "applied",
      "If the Referee does not hear the time-up bell, who blows their whistle?",
      "The Score Supervisor", ["KANSA (the Match Supervisor)", "The Tatami Manager",
       "A corner Judge", "The Chief Referee"],
      "Article 15.6.2: if the Referee does not hear the time-up bell, the Score Supervisor blows the whistle, not KANSA.")

K.lst("Article 15: Powers and Duties of Officials", "15.5.4", 41,
      trues=["The Referee forgets to indicate SENSHU",
             "The Referee gives a score to the wrong athlete",
             "The Referee gives a warning or penalty to the wrong athlete",
             "The Referee gives a score for a technique done after YAME or after time is up",
             "The Referee does not stop the bout when two or more judges signal a score",
             "The Referee does not follow the majority of scores signalled by the judges",
             "The Referee does not call the doctor in a 10-second rule situation",
             "The Referee did not observe a JOGAI"],
      falses=["A judge signals a score that the Referee correctly awards",
              "The coach requests a legitimate video review that is granted",
              "The athletes bow correctly at the start of the bout",
              "The Referee correctly declares the winner at full time",
              "A judge abstains from voting in HANTEI",
              "The doctor treats an injury within the allowed time"],
      expl="Article 15.5.4 lists situations where KANSA (the Match Supervisor) must blow the whistle \u2013 generally when the Referee makes an error in applying the rules.",
      pos_stems=["In which situation must the Match Supervisor (KANSA) blow their whistle?",
                 "Which situation requires KANSA to intervene with a whistle under Article 15.5.4?"],
      neg_stems=["In which situation would KANSA NOT blow their whistle?",
                 "Which of the following is NOT a reason for KANSA to blow the whistle?"])

# ==========================================================================
# KATA
# ==========================================================================
T = Bank("kata", "WKF Kata Competition Rules")

# ---- Article 1: Competition area ----
T.mcq("Article 1: Kata Competition Area", "1.1", 3, "easy",
      ["What are the dimensions of the WKF Kata competition area (matted square), measured from the outside?",
       "The Kata competition area is a matted square with sides of what length?"],
      "Eight metres", ["Six metres", "Ten metres", "Seven metres", "Twelve metres"],
      "Article 1.1: the competition area is a WKF-approved matted square with sides of eight metres, with a clear 2-metre safety area on each side.")
T.mcq("Article 1: Kata Competition Area", "1.1", 3, "theory",
      "How wide is the clear safety area on each side of the Kata competition area?",
      "Two metres", ["One metre", "Three metres", "Half a metre", "Four metres"],
      "Article 1.1: there is a clear safety area of two metres on each side.")
T.mcq("Article 1: Kata Competition Area", "1.2", 3, "hard",
      "From the Judges' table facing the tatami, on which sides are AO and AKA positioned?",
      "AO to the left and AKA to the right", ["AKA to the left and AO to the right",
       "Both on the left", "AO in the centre", "AKA behind the table"],
      "Article 1.2: the Judges sit behind a table facing the middle of the tatami, having AO to the left and AKA to the right.")

# ---- Article 2: Official attire ----
T.mcq("Article 2: Official Attire", "2.2.5", 6, "theory",
      "Which headband is specifically not allowed for Kata athletes?",
      "Hachimaki (headband)", ["A black religious head scarf", "One rubber band on a ponytail",
       "A hairclip", "Two discreet rubber bands"],
      "Article 2.2.5: athletes must keep hair to a length that does not obstruct performance; Hachimaki (headband) is not allowed.")
T.mcq("Article 2: Official Attire", "2.2.6", 6, "applied",
      "Regarding hair ties for Kata athletes, what is permitted?",
      "One or two discreet rubber bands on a single ponytail",
      ["Metal hairgrips", "Decorative ribbons and beads", "Any number of hair slides", "A Hachimaki headband"],
      "Article 2.2.6: hair slides, metal hairgrips, ribbons, beads and decorations are prohibited; one or two discreet rubber bands on a single ponytail is permitted.")
T.mcq("Article 2: Official Attire", "2.2.10", 7, "theory",
      "How much time is a Kata athlete given to correct unauthorised equipment or an irregular Karategi?",
      "One minute", ["Two minutes", "Five minutes", "Thirty seconds", "Three minutes"],
      "Article 2.2.10: athletes with unauthorised equipment or an irregular Karategi are given one minute to correct the attire.")
T.mcq("Article 2: Official Attire", "2.1.2", 4, "hard",
      "Which of these is expressly forbidden for Kata judges within the field of play?",
      "Using phones, smart-watches or private electronic devices, and wearing sunglasses",
      ["Wearing a plain wedding band", "Wearing approved religious headwear",
       "Wearing a hairclip", "Wearing discreet earrings"],
      "Article 2.1.2: it is strictly forbidden for judges to use phones, wear smart-watches or use private electronic devices in the field of play; sunglasses are not allowed.")

# ---- Article 3: Organisation ----
T.mcq("Article 3: Organisation of Kata Competition", "3.1.1", 8, "theory",
      "According to the rules, Kata must NOT be treated as what?",
      "A dance or theatrical performance", ["A martial demonstration",
       "A test of balance and rhythm", "A display of power and speed", "A traditional form"],
      "Article 3.1.1: Kata is not a dance or theatrical performance; it must be realistic in fighting terms and adhere to traditional values.")
T.mcq("Article 3: Organisation of Kata Competition", "3.1.3", 8, "easy",
      "Which competitor performs the Kata first?",
      "The athlete or team designated as AKA (red)", ["The athlete designated as AO (blue)",
       "The higher-ranked athlete", "The athlete on the left", "Whoever the Chief Judge chooses"],
      "Article 3.1.3: the athlete or team designated as AKA performs first.")
T.mcq("Article 3: Organisation of Kata Competition", "3.5.1", 9, "theory",
      "A Kata Team consists of how many athletes, of which how many compete in each round?",
      "3 or 4 athletes, of which 3 compete", ["Exactly 5 athletes, of which 3 compete",
       "Exactly 3 athletes, all of whom compete", "4 or 5 athletes, of which 4 compete",
       "2 or 3 athletes, of which 2 compete"],
      "Article 3.5.1: Kata Teams consist of 3 or 4 athletes, of which 3 compete in each round.")
T.mcq("Article 3: Organisation of Kata Competition", "3.5.6", 9, "hard",
      "What is the total time allowed for the combined Kata and Bunkai demonstration in a Team medal match?",
      "5 minutes", ["3 minutes", "4 minutes", "6 minutes", "2 minutes"],
      "Article 3.5.6: the total time allowed for the Kata and Bunkai demonstration combined is 5 minutes.")
T.mcq("Article 3: Organisation of Kata Competition", "3.5.5", 9, "applied",
      "Between the Kata and the Bunkai in a Team medal match, what happens?",
      "There is no bow \u2013 both are part of the same performance",
      ["The team bows to the judges", "The team bows to each other",
       "There is a one-minute pause", "The team leaves and re-enters"],
      "Article 3.5.5: there is no bow between the Kata and the Bunkai; both elements are part of the same performance.")
T.mcq("Article 3: Organisation of Kata Competition", "3.5.9", 9, "applied",
      "During Bunkai, a scissor takedown (Kani Basami) is prohibited to which area?",
      "The neck", ["The body", "The legs", "The waist", "The shoulder"],
      "Article 3.5.9: a scissor takedown to the neck (Kani Basami) is prohibited during Bunkai, though one to the body or legs is permitted.")
T.mcq("Article 3: Organisation of Kata Competition", "3.5.8", 9, "applied",
      "After being downed while performing Bunkai, within how long should the athlete rise to one knee or stand up?",
      "Within 2 seconds", ["Within 5 seconds", "Within 10 seconds",
       "Within 1 second", "Within 3 seconds"],
      "Article 3.5.8: after being downed, the athlete should rise to one knee or stand up within 2 seconds; playing unconscious is inappropriate.")

# ---- Article 4: Judging panel ----
T.mcq("Article 4: The Judging Panel", "4.1", 13, "hard",
      "How many judges form the panel for each round of Round-robin Kata competition?",
      "Seven judges", ["Five judges", "Three judges", "Nine judges", "Four judges"],
      "Article 4.1: a panel of seven judges is used for each round of Round-robin competition, and five judges for eliminations.")
T.mcq("Article 4: The Judging Panel", "4.1", 13, "hard",
      "How many judges form the panel for elimination rounds in Kata?",
      "Five judges", ["Seven judges", "Three judges", "Four judges", "Nine judges"],
      "Article 4.1: five judges are used for eliminations; seven for each round of Round-robin.")
T.mcq("Article 4: The Judging Panel", "4.9", 13, "applied",
      "If manual judging by flags is used, how many judges officiate and how are they positioned?",
      "Five judges \u2013 four at the corners and one Head Judge centred nearest the official table",
      ["Seven judges around the tatami", "Three judges behind the table",
       "Four judges only at the corners", "Five judges all on one side"],
      "Article 4.9: if manual judging by flags is used, five judges are deployed \u2013 four at the corners and one Head Judge centred at the side closest to the official table.")

# ---- Article 5: Evaluation / scoring ----
T.mcq("Article 5: Evaluation", "5.2.1", 14, "hard",
      "Up to how many different kata may an athlete or team be required to perform in a competition?",
      "Five (5) different kata", ["Three (3) different kata", "Four (4) different kata",
       "Six (6) different kata", "Seven (7) different kata"],
      "Article 5.2.1: no more than five different kata are required; a kata cannot be performed twice in a row, and no kata more than twice.")
T.mcq("Article 5: Evaluation", "5.2.1", 14, "applied",
      "How many times at most may the same kata be performed by an athlete or team in one competition?",
      "Twice", ["Once", "Three times", "Unlimited", "Four times"],
      "Article 5.2.1: no kata can be performed more than twice by an athlete or team in a competition, and never twice in a row.")
T.mcq("Article 5: Evaluation", "5.4.1", 14, "hard",
      "What is the range of the Kata scoring scale, and in what increments?",
      "5.0 to 10.0 in increments of 0.1", ["0.0 to 10.0 in increments of 0.5",
       "1.0 to 10.0 in increments of 0.1", "5.0 to 10.0 in increments of 0.5",
       "6.0 to 10.0 in increments of 0.1"],
      "Article 5.4.1: each performance is scored from 5.0 to 10.0 in increments of 0.1; a disqualification is a 0.0 score.")
T.mcq("Article 5: Evaluation", "5.4.1", 14, "theory",
      "How is a disqualification indicated on the Kata scoring scale?",
      "A score of 0.0", ["A score of 5.0", "A blank score", "A score of 1.0", "A negative score"],
      "Article 5.4.1: a disqualification is indicated by a 0.0 score; 5.0 is the lowest score for an accepted performance.")
T.mcq("Article 5: Evaluation", "5.5.2", 15, "hard",
      "In Kata Round-robin, how many victory points does a team/athlete earn for each bout or match won?",
      "3 Victory points", ["1 Victory point", "2 Victory points", "5 Victory points", "0 Victory points"],
      "Article 5.5.2: the winner earns 3 Victory points and the loser zero; no draws are allowed.")
T.mcq("Article 5: Evaluation", "5.5.3", 15, "theory",
      "On the scoring guideline, a score in the 9\u20139.9 range corresponds to what descriptor?",
      "Excellent", ["Perfect", "Very good", "Good", "Acceptable"],
      "Article 5.5.3: 10 = Perfect, 9\u20139.9 = Excellent, 8\u20138.9 = Very good, 7\u20137.9 = Good, 6\u20136.9 = Acceptable, 5\u20135.9 = Insufficient.")
T.mcq("Article 5: Evaluation", "5.4.2", 14, "applied",
      "In an individual/team bout, how is the winner determined by the judges?",
      "By the majority of votes by the judges", ["By the highest average numeric score",
       "By the Chief Judge alone", "By total victory points only", "By a coin toss"],
      "Article 5.4.2/5.5.1: the winner is determined by the majority of votes by the judges based on relative marks.")

T.lst("Article 5: Evaluation", "5.6", 15,
      trues=["Stances", "Techniques", "Transitional movements",
             "Timing and synchronisation", "Correct breathing", "Focus (KIME)",
             "Strength", "Speed", "Balance"],
      falses=["Loudness of the KIAI alone", "Theatrical facial expression",
              "Height of the athlete", "Length of the performance",
              "Number of techniques performed", "Costume decoration"],
      expl="Article 5.6: Kata performance is evaluated on criteria including stances, techniques, transitional movements, timing/synchronisation, breathing, KIME, conformance, strength, speed and balance.",
      pos_stems=["Which of the following is an official Kata performance evaluation criterion?",
                 "Which is one of the criteria used to evaluate Kata performance?",
                 "Under Article 5.6, which of these is an evaluation criterion?"],
      neg_stems=["Which of the following is NOT a Kata performance evaluation criterion?",
                 "Which of these is NOT used to evaluate a Kata performance?"])

T.lst("Article 5: Evaluation", "5.7", 16,
      trues=["Announcing the kata before, instead of after, the bow",
             "A minor loss of balance",
             "Performing a movement in an incorrect or incomplete manner",
             "Asynchronous movements in Team Kata",
             "Using audible cues to guide the tempo of the performance",
             "Incorrect Kiai",
             "The belt coming loose off the hips during the performance",
             "Time wasting, such as prolonged marching or excessive bowing"],
      falses=["Falling over and having to take a corrective step",
              "Omitting or adding movements",
              "Failing to bow at the beginning of the Kata",
              "Exceeding the 5-minute time limit",
              "A distinct pause or stop in the performance",
              "Belt falling completely off during the performance"],
      expl="Article 5.7 lists fouls (considered in evaluation), which are distinct from Article 5.8 disqualifications. The 'false' items here are actually disqualification reasons, not mere fouls.",
      pos_stems=["Which of the following is treated as a foul (to be considered in evaluation) in Kata?",
                 "Under Article 5.7, which of these is a foul rather than a disqualification?"],
      neg_stems=["Which of the following is a disqualification reason rather than a mere foul?",
                 "Which of these is NOT merely a foul, but a cause for disqualification?"])

T.lst("Article 5: Evaluation", "5.8", 16,
      trues=["Not announcing the kata or performing a different kata than announced",
             "Failing to bow at the beginning and completion of the Kata",
             "Not starting the Kata facing the Judges",
             "A distinct pause or stop in the performance",
             "Omitting or adding movements, substantially changing the performance",
             "Having to take a corrective step to recover from a total loss of balance, or a fall",
             "The belt falling off during the performance",
             "Exceeding the total time limit of 5 minutes",
             "Performing a scissor takedown to the neck in Bunkai (Jodan Kani Basami)"],
      falses=["A minor loss of balance", "A slightly incorrect Kiai",
              "Announcing the kata just before the bow", "Prolonged marching before starting",
              "Asynchronous movements in Team Kata", "The belt loosening but staying on the hips"],
      expl="Article 5.8 lists reasons an athlete or team may be disqualified, distinct from the lesser fouls of Article 5.7.",
      pos_stems=["Which of the following is a reason for disqualification in Kata?",
                 "Under Article 5.8, which of these leads to disqualification?"],
      neg_stems=["Which of the following is a foul rather than a disqualification?",
                 "Which of these would NOT by itself cause disqualification under Article 5.8?"])

# ---- Article 6: Operation of matches ----
T.mcq("Article 6: Operation of Matches", "6.6", 19, "hard",
      "Where a countdown clock is used, how long does an athlete or team have from being announced until the first move after the bow?",
      "35 seconds", ["30 seconds", "45 seconds", "60 seconds", "20 seconds"],
      "Article 6.6: the athlete or team is allowed 35 seconds from being announced on the monitor until the first move after the bow.")
T.mcq("Article 6: Operation of Matches", "6.4", 19, "applied",
      "An athlete or team that does not present themselves when called is disqualified by:",
      "KIKEN", ["SHIKKAKU", "HANSOKU", "HIKIWAKE", "TORIMASEN"],
      "Article 6.4: athletes who do not present themselves when called are disqualified (KIKEN) from that category.")
T.mcq("Article 6: Operation of Matches", "6.5", 19, "theory",
      "Where is the starting point for a Kata performance?",
      "Anywhere within the perimeter of the competition area",
      ["Exactly at the centre of the area", "At the edge nearest the judges",
       "At a marked spot on the tatami", "Just outside the safety area"],
      "Article 6.5: the starting point for the performance is anywhere within the perimeter of the competition area.")
T.mcq("Article 6: Operation of Matches", "6.7", 19, "applied",
      "When must the athlete announce the name of the kata to be performed?",
      "After the bow, before starting the performance",
      ["Before the bow", "After completing the performance",
       "Only if asked by a judge", "During the performance"],
      "Article 6.7: after the bow, the athlete must clearly announce the name of the kata and then start the performance.")
T.mcq("Article 6: Operation of Matches", "6.3", 19, "hard",
      "If there is a discrepancy between the number and the name of a registered kata, which prevails?",
      "The number, as per the official WKF Kata list", ["The name of the kata",
       "The Chief Judge's decision", "Whichever the athlete confirms", "The performance is disqualified"],
      "Article 6.3: where there is a discrepancy between the number and name, the number (per the official WKF Kata list) prevails.")

# ---- Article 7: Protest ----
T.mcq("Article 7: Official Protest", "7.1.2", 20, "theory",
      "Who may make an official protest in Kata competition?",
      "The athlete's Coach or their official representative",
      ["The athlete personally", "Any member of the judging panel",
       "A spectator", "The timekeeper"],
      "Article 7.1.2: only the athlete's Coach or their official representative may make a protest.")
T.mcq("Article 7: Official Protest", "7.1.5", 20, "hard",
      "Within how long after announcing intent to protest must the completed protest form and fee be delivered?",
      "Within 5 minutes", ["Within 10 minutes", "Within 2 minutes",
       "Within 15 minutes", "Within 30 minutes"],
      "Article 7.1.5: the protest form and fee must be completed and delivered within 5 minutes of announcing the intent to protest.")
T.mcq("Article 7: Official Protest", "7.2.1", 21, "hard",
      "How many members make up the Kata Appeals Jury?",
      "Three Senior Referee representatives", ["Five judges", "Two referees",
       "Seven judges", "One Chief Referee"],
      "Article 7.2.1: the Appeals Jury is comprised of three Senior Referee representatives, no two from the same National Federation.")

# ---- Article 8: Eligibility ----
T.mcq("Article 8: Eligibility to Compete", "8.1.2", 23, "hard",
      "In the Senior Kata categories, athletes must be at least how old?",
      "16 years old", ["18 years old", "14 years old", "21 years old", "15 years old"],
      "Article 8.1.2: in the Kata senior categories athletes must be at least 16 years old (whereas Senior Kumite requires 18).")
T.mcq("Article 8: Eligibility to Compete", "8.1.2", 23, "applied",
      "How does the minimum senior age differ between Kata and Kumite?",
      "Senior Kata is 16; Senior Kumite is 18", ["Both are 18",
       "Senior Kata is 18; Senior Kumite is 16", "Both are 16", "Senior Kata is 14; Kumite is 16"],
      "Article 8.1.2: senior Kumite athletes must be 18, while senior Kata athletes must be at least 16.")
T.mcq("Article 8: Eligibility to Compete", "8.1.3", 23, "theory",
      "Participants in the Under-14 Kata categories must be which age?",
      "12 or 13 years old", ["14 or 15 years old", "10 or 11 years old",
       "13 or 14 years old", "11 or 12 years old"],
      "Article 8.1.3: U14 must be 12 or 13; Cadet 14 or 15; Junior 16 or 17; U21 18\u201320.")
T.mcq("Article 8: Eligibility to Compete", "8.3.6", 24, "hard",
      "A naturalised Kata athlete may not represent their new country at the World Championships until how long after naturalisation?",
      "Three years", ["One year", "Two years", "Five years", "Six months"],
      "Article 8.3.6: a naturalised athlete may not compete for their new country until three years after naturalisation (subject to EC reduction).")

# ---- Article 10 / general ----
T.mcq("Article 10: Issues Not Specifically Covered", "Article 10", 26, "applied",
      "When the rules give no specific instruction for a situation, who has the authority to resolve it?",
      "The Chief Referee for the competition", ["The Tatami Manager", "The coaches by agreement",
       "The Appeals Jury", "The WKF President directly"],
      "Article 10: the Chief Referee has authority to resolve issues not covered, by analogy or best judgment, possibly consulting the WKF Representative or Sports Commissioner.")
T.mcq("Article 5: Evaluation", "5.4.3", 15, "theory",
      "In Team medal matches, how is Bunkai weighted relative to the Kata itself?",
      "It is given equal importance to the Kata", ["It is worth half the Kata",
       "It is worth double the Kata", "It is optional and unscored", "It replaces the Kata score"],
      "Article 5.4.3: Bunkai is performed for Team medal matches and is given equal importance to the Kata itself.")
T.mcq("Article 5: Evaluation", "5.7", 16, "applied",
      "Simulated unconsciousness during Bunkai becomes a foul if it lasts longer than what?",
      "2 seconds", ["5 seconds", "10 seconds", "1 second", "3 seconds"],
      "Article 5.7(11): simulated unconsciousness for more than 2 seconds during the Bunkai is a foul.")

# ==========================================================================
# assemble & write
# ==========================================================================

def main():
    kumite = K.build(500, 1)
    kata = T.build(500, 1)
    with open("data/questions-kumite.json", "w") as f:
        json.dump(kumite, f, ensure_ascii=False, indent=1)
    with open("data/questions-kata.json", "w") as f:
        json.dump(kata, f, ensure_ascii=False, indent=1)
    print(f"kumite: {len(kumite)} questions ({len(K.items)} unique authored)")
    print(f"kata:   {len(kata)} questions ({len(T.items)} unique authored)")


if __name__ == "__main__":
    main()
