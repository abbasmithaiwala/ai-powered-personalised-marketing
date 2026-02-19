import React, { useState, type KeyboardEvent } from 'react';
import { XMarkIcon } from '@heroicons/react/20/solid';

interface TagEditorProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
}

export const TagEditor: React.FC<TagEditorProps> = ({
  tags,
  onChange,
  placeholder = 'Add tag...',
}) => {
  const [input, setInput] = useState('');

  const addTag = (value: string) => {
    const trimmed = value.trim().toLowerCase();
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed]);
    }
    setInput('');
  };

  const removeTag = (index: number) => {
    onChange(tags.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(input);
    } else if (e.key === 'Backspace' && !input && tags.length > 0) {
      removeTag(tags.length - 1);
    }
  };

  return (
    <div className="flex flex-wrap gap-1 min-w-[120px]">
      {tags.map((tag, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-700"
        >
          {tag}
          <button
            type="button"
            onClick={() => removeTag(i)}
            className="text-gray-400 hover:text-gray-600 leading-none"
          >
            <XMarkIcon className="h-3 w-3" />
          </button>
        </span>
      ))}
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => { if (input.trim()) addTag(input); }}
        placeholder={tags.length === 0 ? placeholder : ''}
        className="outline-none text-xs min-w-[80px] flex-1 bg-transparent placeholder:text-gray-400"
      />
    </div>
  );
};
