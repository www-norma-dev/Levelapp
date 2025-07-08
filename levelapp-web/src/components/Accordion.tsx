import React, { useState, useRef } from "react";

interface AccordionItem {
  question: string;
  answer: React.ReactNode;
}

const accordionItems: AccordionItem[] = [
  {
    question: "What Is Norma?",
    answer: (
      <>
        <p className="mb-2 text-white">
          Norma is a data and AI engineering company that builds powerful platforms and tools to help organizations deploy,
          evaluate, and scale AI systems responsibly.
        </p>
        <p className="text-white">
          Check out our website{" "}
          <a
            href="https://norma.dev"
            className="text-blue-600 dark:text-blue-500 hover:underline"
          >
            Norma.dev
          </a>
        </p>
      </>
    ),
  },
  {
    question: "What is the Norma Evaluation App?",
    answer: (
      <>
        <p className="mb-2 text-white">
          The Norma Evaluation App is a specialized platform for evaluating multi-agent and LLM-based systems. 
          It helps teams simulate real-world scenarios, run structured batch evaluations, 
          and analyze agent performance using NLP metrics and LLMs as judges.
        </p>
      </>
    ),
  },
  {
    question: "Who is the Evaluation App for?",
    answer: (
      <>
        <p className="mb-2 text-white">
          It’s built for teams developing AI agents, chatbots, or LLM applications, especially where structured evaluation, traceability, 
          and high reliability are critical (e.g., customer support, recommendation systems, or automated workflows).
        </p>
      </>
    ),
  },
];

const Accordion: React.FC = () => {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const contentRefs = useRef<(HTMLDivElement | null)[]>([]);

  const toggleAccordion = (index: number) => {
    setActiveIndex(activeIndex === index ? null : index);
  };

  return (
    <div className="">
      <h1 className="text-3xl text-white text-center font-bold mb-8">
        Got a Question?
      </h1>
      {accordionItems.map((item, index) => (
        <div
          key={index}
          className="border-b border-slate-200  max-w-screen-xl mx-auto"
        >
          <button
            onClick={() => toggleAccordion(index)}
            className="w-full flex justify-between items-center py-5 text-white hover:text-white focus:text-white focus:outline-none"
          >
            <span>{item.question}</span>
            <span className="text-white transition-transform duration-300">
              {activeIndex === index ? "-" : "+"}
            </span>
          </button>
          <div
            ref={(el) => (contentRefs.current[index] = el)}
            className={`overflow-hidden transition-all duration-700 ease-in-out ${
              activeIndex === index ? "max-h-screen" : "max-h-0"
            }`}
          >
            <div className="pb-5 text-sm text-white ">{item.answer}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Accordion;
