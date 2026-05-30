// NOTE: Add pause_pair_presentation_content.md to this repo to replace the placeholder slide bodies below.
// This deck currently uses only the 16 slide titles from the provided content plan plus the required PAUSE/PAIR mnemonic note.

import { useEffect, useMemo, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  FileText,
  HandHeart,
  List,
  Printer,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react';

type Footnote = {
  label: string;
  href: string;
};

type Slide = {
  title: string;
  eyebrow?: string;
  icon: typeof HandHeart;
  accent: 'teal' | 'sage' | 'clay' | 'navy';
  body: string[];
  note?: string;
  footnotes?: Footnote[];
};

const contentPending =
  'Slide content pending. Add pause_pair_presentation_content.md to fill this section from the approved source.';

const mnemonicNote =
  'PAUSE and PAIR are staff-training mnemonics created for this presentation. They organize existing assent-based, trauma-informed, and pairing principles into simple RBT action steps.';

const slides: Slide[] = [
  {
    title: 'PAUSE & PAIR',
    eyebrow: 'Assent-focused RBT action steps',
    icon: HandHeart,
    accent: 'teal',
    body: [contentPending],
    note: mnemonicNote,
    footnotes: [{ label: 'References', href: '#slide-16' }],
  },
  {
    title: 'A Client Should Not Have to Escalate to Be Heard',
    icon: ShieldCheck,
    accent: 'sage',
    body: [contentPending],
    footnotes: [{ label: 'References', href: '#slide-16' }],
  },
  {
    title: 'Assent Is More Than Saying "Yes"',
    icon: CheckCircle2,
    accent: 'clay',
    body: [contentPending],
    footnotes: [{ label: 'References', href: '#slide-16' }],
  },
  {
    title: 'Was a Demand Placed?',
    icon: List,
    accent: 'navy',
    body: [contentPending],
  },
  {
    title: 'PAUSE Is for Demand-Triggered Distress',
    icon: HandHeart,
    accent: 'teal',
    body: [contentPending],
    note: mnemonicNote,
    footnotes: [{ label: 'References', href: '#slide-16' }],
  },
  {
    title: 'PAUSE: What RBTs Do in the Moment',
    icon: HandHeart,
    accent: 'teal',
    body: [contentPending],
    footnotes: [{ label: 'References', href: '#slide-16' }],
  },
  {
    title: 'PAUSE in Action',
    icon: Sparkles,
    accent: 'sage',
    body: [contentPending, 'Keep client examples anonymous when source content is added.'],
  },
  {
    title: 'PAIR Is for Unprompted Distress',
    icon: HandHeart,
    accent: 'clay',
    body: [contentPending],
    note: mnemonicNote,
    footnotes: [{ label: 'References', href: '#slide-16' }],
  },
  {
    title: 'PAIR: What RBTs Do When There Was No Demand',
    icon: HandHeart,
    accent: 'clay',
    body: [contentPending],
    footnotes: [{ label: 'References', href: '#slide-16' }],
  },
  {
    title: 'PAIR in Action',
    icon: Sparkles,
    accent: 'sage',
    body: [contentPending, 'Keep client examples anonymous when source content is added.'],
  },
  {
    title: 'Stimulus Control Means: "What Does This Signal to the Client?"',
    icon: ShieldCheck,
    accent: 'navy',
    body: [contentPending],
    footnotes: [{ label: 'References', href: '#slide-16' }],
  },
  {
    title: 'What Stimulus Control Is Not',
    icon: X,
    accent: 'clay',
    body: [contentPending],
    footnotes: [{ label: 'References', href: '#slide-16' }],
  },
  {
    title: 'Case Pattern: Same Client, Different Signals',
    icon: FileText,
    accent: 'sage',
    body: [contentPending, 'Use anonymous case wording only.'],
  },
  {
    title: 'RBTs Need Visuals in the Room, Not Just Training in a Binder',
    icon: BookOpen,
    accent: 'teal',
    body: [contentPending],
  },
  {
    title: 'A Small Pilot With Big Impact',
    icon: CheckCircle2,
    accent: 'sage',
    body: [contentPending, 'Add only approved pilot details from the source file. Do not add invented numbers.'],
  },
  {
    title: 'References',
    eyebrow: 'Clickable source list',
    icon: BookOpen,
    accent: 'navy',
    body: [
      'References pending. Add pause_pair_presentation_content.md and place each approved citation here as a clickable link.',
    ],
  },
];

const clampSlide = (index: number) => Math.min(Math.max(index, 0), slides.length - 1);

export default function App() {
  const [activeSlide, setActiveSlide] = useState(0);
  const [overviewOpen, setOverviewOpen] = useState(false);

  const slide = slides[activeSlide];
  const Icon = slide.icon;

  const currentHash = useMemo(() => `#slide-${activeSlide + 1}`, [activeSlide]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'ArrowRight' || event.key === 'PageDown') {
        setActiveSlide((current) => clampSlide(current + 1));
      }
      if (event.key === 'ArrowLeft' || event.key === 'PageUp') {
        setActiveSlide((current) => clampSlide(current - 1));
      }
      if (event.key === 'Home') {
        setActiveSlide(0);
      }
      if (event.key === 'End') {
        setActiveSlide(slides.length - 1);
      }
      if (event.key === 'Escape') {
        setOverviewOpen(false);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  useEffect(() => {
    window.history.replaceState(null, '', currentHash);
  }, [currentHash]);

  const goToSlide = (index: number) => {
    setActiveSlide(clampSlide(index));
    setOverviewOpen(false);
  };

  return (
    <main className="deck-app">
      <section className="presentation-shell" aria-live="polite">
        <article className={`slide-canvas accent-${slide.accent}`} id={`slide-${activeSlide + 1}`}>
          <div className="slide-header">
            <div className="slide-mark" aria-hidden="true">
              <Icon size={30} strokeWidth={1.8} />
            </div>
            <div>
              <p className="slide-kicker">PAUSE & PAIR</p>
              {slide.eyebrow ? <p className="slide-eyebrow">{slide.eyebrow}</p> : null}
            </div>
          </div>

          <div className="slide-content">
            <h1>{slide.title}</h1>
            <div className="body-grid">
              {slide.body.map((item) => (
                <p key={item}>{item}</p>
              ))}
            </div>
            {slide.note ? <aside className="mnemonic-note">{slide.note}</aside> : null}
          </div>

          <footer className="slide-footer">
            <div className="footnotes" aria-label="Slide citations">
              {slide.footnotes?.map((footnote) => (
                <a key={footnote.label} href={footnote.href}>
                  {footnote.label}
                </a>
              ))}
            </div>
            <span>
              {String(activeSlide + 1).padStart(2, '0')} / {String(slides.length).padStart(2, '0')}
            </span>
          </footer>
        </article>
      </section>

      <nav className="speaker-controls" aria-label="Presentation controls">
        <button type="button" onClick={() => goToSlide(activeSlide - 1)} disabled={activeSlide === 0}>
          <ArrowLeft size={20} />
          <span>Previous</span>
        </button>
        <button type="button" className="counter-button" onClick={() => setOverviewOpen(true)}>
          <List size={20} />
          <span>
            Slide {activeSlide + 1} of {slides.length}
          </span>
        </button>
        <button type="button" onClick={() => window.print()}>
          <Printer size={20} />
          <span>Print PDF</span>
        </button>
        <button
          type="button"
          onClick={() => goToSlide(activeSlide + 1)}
          disabled={activeSlide === slides.length - 1}
        >
          <span>Next</span>
          <ArrowRight size={20} />
        </button>
      </nav>

      {overviewOpen ? (
        <div className="overview-backdrop" role="presentation" onClick={() => setOverviewOpen(false)}>
          <aside
            className="overview-drawer"
            aria-label="Slide overview"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="overview-heading">
              <h2>Slides</h2>
              <button type="button" onClick={() => setOverviewOpen(false)} aria-label="Close slide overview">
                <X size={20} />
              </button>
            </div>
            <ol>
              {slides.map((item, index) => (
                <li key={item.title}>
                  <button
                    type="button"
                    className={index === activeSlide ? 'is-active' : ''}
                    onClick={() => goToSlide(index)}
                  >
                    <span>{String(index + 1).padStart(2, '0')}</span>
                    {item.title}
                  </button>
                </li>
              ))}
            </ol>
          </aside>
        </div>
      ) : null}

      <div className="print-deck" aria-hidden="true">
        {slides.map((item, index) => {
          const PrintIcon = item.icon;
          return (
            <article className={`slide-canvas print-slide accent-${item.accent}`} id={`print-slide-${index + 1}`} key={item.title}>
              <div className="slide-header">
                <div className="slide-mark" aria-hidden="true">
                  <PrintIcon size={30} strokeWidth={1.8} />
                </div>
                <div>
                  <p className="slide-kicker">PAUSE & PAIR</p>
                  {item.eyebrow ? <p className="slide-eyebrow">{item.eyebrow}</p> : null}
                </div>
              </div>
              <div className="slide-content">
                <h1>{item.title}</h1>
                <div className="body-grid">
                  {item.body.map((bodyItem) => (
                    <p key={bodyItem}>{bodyItem}</p>
                  ))}
                </div>
                {item.note ? <aside className="mnemonic-note">{item.note}</aside> : null}
              </div>
              <footer className="slide-footer">
                <div className="footnotes">
                  {item.footnotes?.map((footnote) => (
                    <a key={footnote.label} href={footnote.href}>
                      {footnote.label}
                    </a>
                  ))}
                </div>
                <span>
                  {String(index + 1).padStart(2, '0')} / {String(slides.length).padStart(2, '0')}
                </span>
              </footer>
            </article>
          );
        })}
      </div>
    </main>
  );
}
