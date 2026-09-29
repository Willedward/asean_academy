import { PREVIEW_ROUTES, preview } from "../routes";
import { samplePlayer } from "../sample-data";
import {
  EnglishHomeScreen,
  EssayEditorScreen,
  EssayFeedbackScreen,
  EssayHistoryScreen,
  EssayMarkingScreen,
  EssayPromptScreen,
  EssaySubmitScreen,
  Gap,
  GrammarQuestionScreen,
  VocabQuestionScreen,
  type CriterionFeedback,
  type EssayDraft,
  type EssayFix,
  type GrammarChoice,
  type GrammarUnitSummary,
  type WritingTask,
  type WritingTaskSummary,
} from "../screens/english";
import type { Quest } from "../types";
import type { PreviewEntry } from "./registry";

/* ------------------------------------------------------------------ */
/* Sample data (copy from the design canvas, screens5.py and gamify.py) */
/* ------------------------------------------------------------------ */

const englishHome = preview("english");
const subjectLinks = { maths: PREVIEW_ROUTES.nav.course, english: englishHome };

const englishQuests: Quest[] = [
  { id: "grammar-10", title: "Answer 10 grammar questions", icon: "check", progress: 6, target: 10, xp: 15 },
  { id: "draft-100", title: "Write 100 words of a draft", icon: "file", progress: 100, target: 100, xp: 15 },
];

const grammarUnits: GrammarUnitSummary[] = [
  { key: "subject-verb", title: "Subject and verb agreement", questionCount: 12, state: "proficient", stars: 2, href: preview("grammar-question") },
  { key: "tenses", title: "Tenses", questionCount: 15, state: "practising", stars: 1, href: preview("grammar-question") },
  { key: "prepositions", title: "Prepositions", questionCount: 10, state: "ready", stars: 0, xpAvailable: 40, href: preview("grammar-question") },
  { key: "words-in-context", title: "Words in context", questionCount: 14, state: "ready", stars: 0, xpAvailable: 40, href: preview("vocab-question") },
];

const writingTasks: WritingTaskSummary[] = [
  {
    key: "reading-corner",
    kind: "Situational writing",
    title: "Email to your principal about a reading corner",
    words: { min: 250, max: 350 },
    minutes: 45,
    status: "draft",
    submitXp: 30,
    improveXp: 20,
    href: preview("essay-editor"),
  },
  {
    key: "changed-mind",
    kind: "Continuous writing",
    title: "A time you changed your mind",
    words: { min: 350, max: 500 },
    minutes: 60,
    status: "new",
    submitXp: 30,
    improveXp: 20,
    href: preview("essay-prompt"),
  },
  {
    key: "charity-fair",
    kind: "Situational writing",
    title: "Report on the class charity fair",
    words: { min: 250, max: 350 },
    minutes: 45,
    status: "marked",
    marked: { dateLabel: "18 Sep", score: 21, outOf: 30 },
    submitXp: 30,
    improveXp: 20,
    href: preview("essay-feedback"),
  },
];

const readingCorner: WritingTask = {
  key: "reading-corner",
  kind: "Situational writing",
  title: "Email to your principal about a reading corner",
  brief:
    "Your school library is opening a reading corner next term, but few students visit the library now. Write an email to your principal, Mrs Tan, suggesting two ways to make the reading corner popular.",
  purpose: "Suggest two ways to make the new reading corner popular, and give a reason for each.",
  audience: "Mrs Tan, your principal. Keep it polite and formal.",
  context: "The school library is opening a reading corner next term. Few students visit the library now.",
  words: { min: 250, max: 350 },
  minutes: 45,
  formatNoun: "email",
  rubric: [
    { name: "Task fulfilment", marks: 10 },
    { name: "Language and organisation", marks: 20 },
  ],
  rubricHref: preview("essay-prompt"),
};

const DRAFT = [
  "Dear Mrs Tan,",
  "I am writing to suggest two ways to make the new reading corner popular with students. At the moment, many of my classmates only visit the library when a teacher tells them to, and I think a few small changes could help.",
  "Firstly, the school could hold a book swap every Friday. Students can bring a book they have finished and take a new one home. This make reading free and fun, and the students is more interested when they choose the books themselves. It would also help students who cannot afford to buy many books, because they can still read something new every single week.",
  "Secondly, I suggest putting comfortable bean bags in the corner and a small board where students recommend books to each other. When we see what our friends are reading, we want to try it too. Each class could take turns to update the board, so that it always has fresh ideas and every student feels that the corner belongs to them. The board would also help new students, who often do not know which books suit their age and interests.",
  "I believe these two ideas are cheap and simple to start. They would make the reading corner a place where students want to spend their breaks, not a place they walk past. Many of my friends have already said they would bring books to swap if the school allowed it.",
  "Thank you for reading my email. I hope you will consider",
];

const WORDS = DRAFT.reduce((sum, para) => sum + para.split(/\s+/).filter(Boolean).length, 0);

const draft: EssayDraft = {
  version: 1,
  text: DRAFT.join("\n\n"),
  wordCount: WORDS,
  savedLabel: "10 s ago",
  restoredNotice: "We found a newer version from your phone, saved 5 minutes ago, and opened it here.",
};

const editorProps = {
  player: samplePlayer,
  task: readingCorner,
  draft,
  submitXp: 30,
  backHref: englishHome,
  submitHref: preview("essay-submit"),
};

const CHOICES: GrammarChoice[] = [
  { id: "is", label: "is" },
  { id: "are", label: "are" },
  { id: "was", label: "was" },
  { id: "has-been", label: "has been" },
];

const grammarBase = {
  player: samplePlayer,
  topic: "Subject and verb agreement",
  position: 5,
  total: 12,
  instruction: "Choose the word that completes the sentence.",
  choices: CHOICES,
  firstTryXp: 10,
  retryXp: 6,
  closeHref: englishHome,
  nextHref: englishHome,
};

const stem = (value?: string) => (
  <>
    Neither the teacher nor the students <Gap value={value} /> ready for the test.
  </>
);

const fixes: EssayFix[] = [
  {
    title: "Finish your closing",
    body: "Your last line stops mid-sentence: “I hope you will consider”. End with a full request and a sign-off, for example “I hope you will consider these ideas. Yours sincerely, Dimas.”",
  },
  {
    title: "Check subject and verb",
    body: (
      <>
        Two slips: “This make reading free” should be “This <b>makes</b> reading free”, and “the students is” should be “the students <b>are</b>”.
      </>
    ),
  },
  { title: "Add one practical detail", body: "Say who could run the book swap, such as the library club, so Mrs Tan can picture it working." },
];

const criteria: CriterionFeedback[] = [
  {
    name: "Task fulfilment",
    score: 7,
    outOf: 10,
    level: "Good",
    levelTone: "brand",
    summary: "You gave two clear suggestions, each with a reason.",
    quote: "the school could hold a book swap every Friday",
    followUp: "Missing: you did not say who would run the book swap or when it would start.",
  },
  {
    name: "Language and organisation",
    score: 12,
    outOf: 20,
    level: "Developing",
    levelTone: "amber",
    summary: "Clear paragraphs and a polite tone. A few grammar slips pull the mark down.",
    quote: "the students is more interested",
    followUp: (
      <>
        &quot;Students&quot; is plural, so write <b>the students are</b>.
      </>
    ),
  },
];

/* ------------------------------------------------------------------ */
/* Entries                                                             */
/* ------------------------------------------------------------------ */

export const englishEntries: PreviewEntry[] = [
  {
    key: "english",
    title: "English home",
    group: "English",
    canvas: ["EnglishHome.m", "EnglishHome.d"],
    render: () => (
      <EnglishHomeScreen
        player={samplePlayer}
        subjectLinks={subjectLinks}
        quests={englishQuests}
        questsResetIn="6h"
        essayMarksLeft={3}
        grammarUnits={grammarUnits}
        writingTasks={writingTasks}
        myEssaysHref={preview("essay-history")}
      />
    ),
  },
  {
    key: "grammar-question",
    title: "Grammar question",
    group: "English",
    canvas: ["GrammarQuestion.m"],
    render: () => (
      <GrammarQuestionScreen
        {...grammarBase}
        state="answering"
        stem={stem()}
        selectedId="are"
        wrongIds={[]}
        checkHref={preview("grammar-wrong")}
      />
    ),
  },
  {
    key: "grammar-wrong",
    title: "Grammar, wrong answer",
    group: "English",
    canvas: ["GrammarWrong.m"],
    render: () => (
      <GrammarQuestionScreen
        {...grammarBase}
        state="wrong"
        stem={stem()}
        selectedId={null}
        wrongIds={["is"]}
        reason="Look at which subject is closer to the gap."
      />
    ),
  },
  {
    key: "grammar-right",
    title: "Grammar, right answer",
    group: "English",
    canvas: ["GrammarRight.m"],
    render: () => (
      <GrammarQuestionScreen
        {...grammarBase}
        state="right"
        headerTopic="Verb agreement"
        stem={stem("are")}
        selectedId="are"
        wrongIds={[]}
        correctId="are"
        earnedXp={10}
        combo={3}
        questProgress={{ id: "grammar-10", title: "Answer 10 grammar questions", icon: "check", progress: 7, target: 10, xp: 15 }}
        reason={
          <>
            With <i>neither … nor</i>, the verb agrees with the nearer subject. &quot;Students&quot; is plural, so use <b>are</b>.
          </>
        }
      />
    ),
  },
  {
    key: "vocab-question",
    title: "Vocabulary, typed answer",
    group: "English",
    canvas: ["VocabQuestion.m"],
    render: () => (
      <VocabQuestionScreen
        player={samplePlayer}
        topic="Words in context"
        position={9}
        total={14}
        instruction="Type the word that fits. One word only."
        stem={
          <>
            Mei was <b>reluctant</b> to speak at first, but she soon grew more ______ as the discussion went on.
          </>
        }
        hint={
          <>
            Hint: the opposite of reluctant, starting with <b>c</b>.
          </>
        }
        answer="confident"
        firstTryXp={10}
        closeHref={englishHome}
        checkHref={preview("grammar-right")}
      />
    ),
  },
  {
    key: "essay-prompt",
    title: "Essay task",
    group: "English",
    canvas: ["EssayPrompt.m"],
    render: () => (
      <EssayPromptScreen
        player={samplePlayer}
        task={readingCorner}
        submitXp={30}
        firstEssayBadge="Essay starter"
        backHref={englishHome}
        startHref={preview("essay-editor")}
      />
    ),
  },
  {
    key: "essay-editor",
    title: "Essay editor",
    group: "English",
    canvas: ["EssayEditor.m", "EssayEditor.d"],
    render: () => <EssayEditorScreen {...editorProps} />,
  },
  {
    key: "essay-submit",
    title: "Essay, submit sheet",
    group: "English",
    canvas: ["EssaySubmit.m"],
    render: () => (
      <EssaySubmitScreen
        {...editorProps}
        draft={{ ...draft, restoredNotice: undefined }}
        checks={[
          { ok: true, text: `${WORDS} words, inside 250 to 350` },
          { ok: false, text: "Your last sentence looks unfinished" },
          { ok: false, text: "You have 3 essay marks left. This uses 1." },
        ]}
        rewardNote="Plus the Essay starter badge for your first one."
        confirmHref={preview("essay-marking")}
        keepWritingHref={preview("essay-editor")}
      />
    ),
  },
  {
    key: "essay-marking",
    title: "Essay being marked",
    group: "English",
    canvas: ["EssayMarking.m"],
    render: () => (
      <EssayMarkingScreen
        player={samplePlayer}
        formatNoun="email"
        submitXp={30}
        steps={[
          { label: "Submitted and locked", state: "done" },
          { label: "Reading your email against the rubric", state: "now" },
          { label: "Writing your feedback", state: "next" },
        ]}
        version={{ number: 1, wordCount: WORDS, submittedLabel: "today, 20:14", href: preview("essay-editor") }}
        practiseXp={10}
        practiseHref={preview("grammar-question")}
        backHref={englishHome}
      />
    ),
  },
  {
    key: "essay-feedback",
    title: "Essay feedback",
    group: "English",
    canvas: ["EssayFeedback.m", "EssayFeedback.d"],
    render: () => (
      <EssayFeedbackScreen
        player={samplePlayer}
        task={readingCorner}
        version={{ number: 1, paragraphs: DRAFT, wordCount: WORDS, submittedLabel: "today, 20:14" }}
        highlights={["This make reading", "the students is more interested"]}
        score={{ total: 19, outOf: 30, label: "Good, not yet strong" }}
        fixes={fixes}
        practise={{ label: "Practise subject and verb agreement", href: preview("grammar-question") }}
        criteria={criteria}
        strengths={[
          "Your opening states the purpose in one sentence.",
          "The bean bags and recommendation board idea is specific and easy to picture.",
        ]}
        badgeWon={{ name: "Essay starter", icon: "star", tier: "bronze", message: "Your first essay is in. +30 XP added.", xp: 30 }}
        improveXp={20}
        rating={null}
        writeNextHref={preview("essay-editor")}
        modelAnswerHref={preview("essay-prompt")}
        essayHref={preview("essay-history")}
        reportHref={preview("report-problem")}
        backHref={preview("essay-history")}
      />
    ),
  },
  {
    key: "essay-history",
    title: "My essays",
    group: "English",
    canvas: ["EssayHistory.m"],
    render: () => (
      <EssayHistoryScreen
        player={samplePlayer}
        backHref={englishHome}
        essays={[
          { key: "rc-1", title: "Email to your principal about a reading corner", status: "marking", version: 1, dateLabel: "today", href: preview("essay-marking") },
          { key: "cf-2", title: "Report on the class charity fair", status: "marked", version: 2, dateLabel: "18 Sep", score: { total: 21, outOf: 30 }, href: preview("essay-feedback") },
          { key: "cf-1", title: "Report on the class charity fair", status: "marked", version: 1, dateLabel: "11 Sep", score: { total: 16, outOf: 30 }, href: preview("essay-feedback") },
          { key: "cm-draft", title: "A time you changed your mind", status: "draft", version: null, dateLabel: "3 days ago", wordCount: 40, href: preview("essay-editor") },
        ]}
        improvement={{ marks: 5, taskLabel: "charity fair report", from: 1, to: 2, xp: 20 }}
      />
    ),
  },
];
