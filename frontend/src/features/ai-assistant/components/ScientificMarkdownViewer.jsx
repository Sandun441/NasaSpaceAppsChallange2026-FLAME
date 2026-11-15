import React from 'react';

/**
 * Cleans scientific unicode artifacts and mojibake encodings.
 * Eliminates Â°C -> °C, mw/cmÂ² -> mW/cm², â¢ -> •, etc.
 */
export function cleanScientificUnicode(text) {
  if (!text || typeof text !== 'string') return text;
  return text
    .replace(/mw\/cmÂ²/gi, 'mW/cm²')
    .replace(/mW\/cmÂ²/g, 'mW/cm²')
    .replace(/Â°C/g, '°C')
    .replace(/Â°F/g, '°F')
    .replace(/Â°/g, '°')
    .replace(/cmÂ²/g, 'cm²')
    .replace(/Â²/g, '²')
    .replace(/Â³/g, '³')
    .replace(/Â±/g, '±')
    .replace(/â€¢/g, '•')
    .replace(/â¢/g, '•')
    .replace(/â€“/g, '–')
    .replace(/â€”/g, '—')
    .replace(/â€˜/g, "'")
    .replace(/â€™/g, "'")
    .replace(/â€œ/g, '"')
    .replace(/â€/g, '"');
}

/**
 * Parses inline formatting:
 * - Bold: **text**
 * - Italic: *text*
 * - Code: `code`
 * - Citations: [flame_...]
 */
function renderInlineFormatting(text) {
  if (!text) return null;

  // Tokenize by citation [flame_...], bold **...**, code `...`, and italic *...*
  const tokenRegex = /(\[flame_[a-zA-Z0-9_]+\]|\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  const parts = text.split(tokenRegex);

  return parts.map((part, idx) => {
    if (!part) return null;

    // Citations
    if (part.startsWith('[flame_') && part.endsWith(']')) {
      const cid = part.slice(1, -1);
      return (
        <span
          key={idx}
          className="inline-flex items-center gap-1 px-1.5 py-0.5 mx-0.5 rounded bg-orange-50 text-orange-700 font-mono text-[10px] border border-orange-200 hover:border-orange-300 hover:bg-orange-100 transition-all cursor-default select-all"
          title={`NASA FLAME Verified Record ID: ${cid}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
          {cid}
        </span>
      );
    }

    // Bold
    if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
      return (
        <strong key={idx} className="font-semibold text-slate-900">
          {renderInlineFormatting(part.slice(2, -2))}
        </strong>
      );
    }

    // Code
    if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
      return (
        <code
          key={idx}
          className="font-mono text-[11px] bg-slate-100 text-slate-800 px-1.5 py-0.5 rounded border border-slate-200"
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    // Italic
    if (part.startsWith('*') && part.endsWith('*') && part.length >= 2) {
      return (
        <em key={idx} className="italic text-slate-600">
          {part.slice(1, -1)}
        </em>
      );
    }

    return part;
  });
}

/**
 * ScientificMarkdownViewer
 * Zero-dependency, safe Markdown and scientific structured renderer for NASA FLAME.
 * Parses headers, tables, bullet/nested lists, blockquotes, code blocks, and citations.
 */
export function ScientificMarkdownViewer({ content = '' }) {
  if (!content) return null;

  const sanitizedContent = cleanScientificUnicode(content);
  const lines = sanitizedContent.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // 1. Skip empty lines
    if (!trimmed) {
      i++;
      continue;
    }

    // 2. Markdown Table Detection (Line starts and ends with '|')
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
        tableLines.push(lines[i].trim());
        i++;
      }

      if (tableLines.length >= 2) {
        const headerRow = tableLines[0]
          .slice(1, -1)
          .split('|')
          .map((col) => col.trim());

        // Line 1 is the delimiter row (e.g. | :--- | :--- |)
        const bodyRows = tableLines.slice(2).map((rowLine) =>
          rowLine
            .slice(1, -1)
            .split('|')
            .map((col) => col.trim())
        );

        elements.push(
          <div key={`table_${i}`} className="overflow-x-auto my-4 rounded-xl border border-slate-200 bg-white shadow-xs">
            <table className="w-full text-left text-xs font-mono divide-y divide-slate-200">
              <thead className="bg-slate-50 text-slate-700">
                <tr>
                  {headerRow.map((h, colIdx) => (
                    <th key={colIdx} className="px-3.5 py-2.5 font-semibold text-orange-700 uppercase tracking-wider text-[11px]">
                      {renderInlineFormatting(h)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {bodyRows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-slate-50 transition-colors">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="px-3.5 py-2 leading-relaxed">
                        {renderInlineFormatting(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // 3. Headings
    if (trimmed.startsWith('#### ')) {
      elements.push(
        <h5 key={`h4_${i}`} className="text-xs font-semibold text-slate-800 mt-3 mb-1">
          {renderInlineFormatting(trimmed.slice(5))}
        </h5>
      );
      i++;
      continue;
    }

    if (trimmed.startsWith('### ')) {
      elements.push(
        <h4 key={`h3_${i}`} className="text-xs sm:text-sm font-bold text-orange-600 mt-4 mb-2 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
          {renderInlineFormatting(trimmed.slice(4))}
        </h4>
      );
      i++;
      continue;
    }

    if (trimmed.startsWith('## ')) {
      elements.push(
        <h3 key={`h2_${i}`} className="text-sm sm:text-base font-bold text-slate-900 mt-5 mb-2 pb-1 border-b border-slate-200">
          {renderInlineFormatting(trimmed.slice(3))}
        </h3>
      );
      i++;
      continue;
    }

    if (trimmed.startsWith('# ')) {
      elements.push(
        <h2 key={`h1_${i}`} className="text-base sm:text-lg font-bold text-slate-900 mt-5 mb-3 pb-1.5 border-b border-slate-200">
          {renderInlineFormatting(trimmed.slice(2))}
        </h2>
      );
      i++;
      continue;
    }

    // 4. Blockquotes / Alerts (> ...)
    if (trimmed.startsWith('> ')) {
      elements.push(
        <div key={`quote_${i}`} className="my-3 p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs leading-relaxed font-sans">
          {renderInlineFormatting(trimmed.slice(2))}
        </div>
      );
      i++;
      continue;
    }

    // 5. Lists (unordered - or *)
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const listItems = [];
      while (i < lines.length && (lines[i].trim().startsWith('- ') || lines[i].trim().startsWith('* '))) {
        const itemLine = lines[i];
        const isIndented = itemLine.startsWith('  ') || itemLine.startsWith('\t');
        listItems.push({
          text: itemLine.trim().slice(2),
          isIndented,
        });
        i++;
      }

      elements.push(
        <ul key={`list_${i}`} className="space-y-1.5 my-2.5 pl-1">
          {listItems.map((item, idx) => (
            <li
              key={idx}
              className={`flex items-start gap-2.5 text-xs sm:text-sm leading-relaxed ${
                item.isIndented ? 'ml-5 text-slate-600' : 'text-slate-700'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${item.isIndented ? 'bg-slate-400' : 'bg-orange-500'}`} />
              <div className="flex-1">{renderInlineFormatting(item.text)}</div>
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 6. Default paragraph
    elements.push(
      <p key={`p_${i}`} className="text-xs sm:text-sm leading-relaxed text-slate-700 my-2">
        {renderInlineFormatting(trimmed)}
      </p>
    );
    i++;
  }

  return (
    <div className="space-y-2 text-slate-800 font-sans">
      {elements}
    </div>
  );
}
