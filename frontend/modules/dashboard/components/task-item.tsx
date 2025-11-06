'use client'

import { useState } from 'react';
import { Circle, CheckCircle2 } from 'lucide-react';
import { Task } from '@/lib/types';
import clsx from 'clsx';

interface TaskItemProps {
  task: Task;
  bordered?: boolean;
}

export function TaskItem({ task, bordered }: TaskItemProps) {
  const [completed, setCompleted] = useState(task.status === 'completed');

  const toggle = () => {
    setCompleted((c) => !c);
  };

  return (
    <div
      onClick={toggle}
      className={clsx(
        'flex items-start gap-3 px-6 py-4 min-h-[72px] cursor-pointer transition-colors',
        bordered && 'border-b border-gray-200',
        completed && 'bg-lintblauw/10'
      )}
    >
      {completed ? (
        <CheckCircle2 className="h-5 w-5 flex-shrink-0 mt-0.5 text-lintblauw transition" />
      ) : (
        <Circle className="h-5 w-5 flex-shrink-0 mt-0.5 text-gray-400 transition" />
      )}
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-center">
          <p className="font-semibold text-base text-black leading-tight">
            {task.title}
          </p>
          {/* Badge with due date */}
          {task.dueDate && (
            <span className="text-gray-500 text-sm">
              {new Date(task.dueDate).toLocaleDateString('nl-NL', {
                day: '2-digit',
                month: 'long',
              })}
            </span>
          )}
        </div>
        {task.relatedTo && (
          <a
            href={task.relatedTo.url}
            className="text-xs text-lintblauw underline block mt-0.5"
            target="_blank"
            rel="noopener noreferrer"
          >
            &uarr; {task.relatedTo.title}
          </a>
        )}
      </div>
    </div>
  );
}
