'use client';

import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StepperProps {
  currentStep: number;
  steps: string[];
}

export function Stepper({ currentStep, steps }: StepperProps) {
  return (
    <div className="w-full ">
      <div className="relative flex justify-between">
        {steps.map((step, index) => (
          <div key={step} className="flex flex-col items-center">
            <div
              className={cn(
                'w-10 h-10 rounded-full border-2 flex items-center justify-center',
                currentStep > index
                  ? 'bg-primary text-primary-foreground border-primary'
                  : currentStep === index
                  ? 'border-primary text-primary'
                  : 'border-muted-foreground text-muted-foreground'
              )}
            >
              {currentStep > index ? <Check className="w-5 h-5" /> : <span>{index + 1}</span>}
            </div>
            <span className={cn('mt-2 text-sm', currentStep >= index ? 'text-primary' : 'text-muted-foreground')}>
              {step}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
