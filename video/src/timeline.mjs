/** Pure frame arithmetic. No clock, random data, network or number recalculation. */
export function buildTimeline(chapters) {
  let fromFrame = 0;
  const items = chapters.map((chapter, index) => {
    const item = {chapter, index, fromFrame, durationInFrames: chapter.durationInFrames};
    fromFrame += chapter.durationInFrames;
    return item;
  });
  return {chapters: items, durationInFrames: fromFrame};
}

export function currentSegment(chapter, frame) {
  let current = null;
  for (const segment of chapter.segments) {
    if (segment.fromFrame > frame) break;
    current = segment;
  }
  return current;
}

export function captionPages(text, limit = 165) {
  const words = String(text || '').trim().split(/\s+/).filter(Boolean);
  const pages = [];
  let page = '';
  for (const word of words) {
    if (page && page.length + word.length + 1 > limit) {
      pages.push(page);
      page = '';
    }
    // A long individual token is retained and wraps; the report is never edited.
    page += (page ? ' ' : '') + word;
  }
  if (page) pages.push(page);
  return pages;
}

export function captionAt(segment, frame, limit = 165) {
  if (!segment) return {text: '', index: 0, count: 0};
  const pages = captionPages(segment.text, limit);
  if (!pages.length) return {text: '', index: 0, count: 0};
  const elapsed = Math.max(0, Math.min(segment.durationInFrames - 1, frame - segment.fromFrame));
  const total = pages.reduce((sum, page) => sum + page.length, 0);
  const position = (elapsed / segment.durationInFrames) * total;
  let boundary = 0;
  const index = pages.findIndex((page) => {boundary += page.length; return position < boundary;});
  const selected = index < 0 ? pages.length - 1 : index;
  const before = pages.slice(0, selected).reduce((sum, page) => sum + page.length, 0);
  return {text: pages[selected], index: selected, count: pages.length,
    fromFrame: segment.fromFrame + Math.round(before / total * segment.durationInFrames),
    durationInFrames: Math.max(1, Math.round(pages[selected].length / total * segment.durationInFrames))};
}

/** Focus is a separate track: several spoken numbers may occur in one caption. */
export function focusTimeline(chapter) {
  const total = chapter.section?.diagram?.entries?.length || chapter.section?.values?.length || chapter.section?.chart?.items?.length || 0;
  const valid = (index) => Number.isInteger(index) && index >= 0 && index < total ? index : null;
  const events = [{fromFrame: 0, focusIndex: null}];
  const add = (fromFrame, index) => {
    const focusIndex = valid(index);
    if (events.at(-1).fromFrame === fromFrame) events.pop();
    if (!events.length || events.at(-1).focusIndex !== focusIndex) events.push({fromFrame, focusIndex});
  };
  for (const segment of chapter.segments) {
    if (segment.focusCues?.length) {
      add(segment.fromFrame, null);
      for (const cue of segment.focusCues) {
        add(cue.fromFrame, cue.focusIndex);
        const end = cue.fromFrame + cue.durationInFrames;
        if (end < segment.fromFrame + segment.durationInFrames) add(end, null);
      }
    } else add(segment.fromFrame, segment.focusIndex);
  }
  return events;
}

export function focusAt(chapter, frame) {
  const events = focusTimeline(chapter);
  let current = {fromFrame: 0, focusIndex: null}, previous = null;
  for (const event of events) {
    if (event.fromFrame > frame) break;
    previous = current.focusIndex; current = event;
  }
  const next = events.find((event) => event.fromFrame > frame);
  return {focusIndex: current.focusIndex, previousFocusIndex: previous, focusFromFrame: current.fromFrame,
    focusDuration: (next?.fromFrame ?? chapter.durationInFrames) - current.fromFrame,
    focusAge: Math.max(0, frame - current.fromFrame), focusEvents: events};
}

export function pageWindow(total, focusIndex, size = 7, frame = 0, duration = 1) {
  if (total === 0) return {start: 0, end: 0, activeIndex: null};
  const activeIndex = Number.isInteger(focusIndex) && focusIndex >= 0 && focusIndex < total ? focusIndex : null;
  if (total <= size) return {start: 0, end: total, activeIndex};
  const pages = Math.ceil(total / size);
  const page = Math.min(pages - 1, Math.floor(Math.max(0, frame) / Math.max(1, duration) * pages));
  const start = activeIndex === null ? Math.min(page * size, total - size)
    : Math.max(0, Math.min(total - size, activeIndex - Math.floor(size / 2)));
  return {start, end: Math.min(total, start + size), activeIndex};
}

export function sceneModel(chapter, frame) {
  const segment = currentSegment(chapter, frame);
  const section = chapter.section;
  const items = section?.chart?.items ?? section?.values ?? [];
  const directing = focusAt(chapter, frame), focus = directing.focusIndex;
  return {
    segment,
    caption: captionAt(segment, frame),
    ...directing,
    items,
    window: pageWindow(items.length, focus, section?.chart?.type === 'matrix' ? 9 : 7, frame, chapter.durationInFrames),
    value: focus === null ? null : section?.values?.[focus] ?? null,
  };
}
