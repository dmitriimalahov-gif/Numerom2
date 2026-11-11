import React, { useCallback, useEffect, useRef, useState } from 'react';
import '../styles/living-logo.css';

const AWAKENING_MS = 4400;
const NAME = 'NumerOM — Numbers Reveal';

/** Decoration remains separate from the canonical, transparent brand artwork. */
export const Brand = ({ compact = false, tone = 'auto' }) => {
  const element = useRef(null);
  const timeout = useRef(null);
  const playing = useRef(false);
  const sequence = useRef(0);
  const [reducedMotion, setReducedMotion] = useState(true);
  const [standalone, setStandalone] = useState(false);
  const [awake, setAwake] = useState(false);
  const [palette, setPalette] = useState(0);

  const settle = useCallback(() => {
    clearTimeout(timeout.current);
    playing.current = false;
    setAwake(false);
  }, []);

  const awaken = useCallback(() => {
    if (compact || reducedMotion || playing.current || document.hidden) return;
    playing.current = true;
    setPalette(sequence.current++ % 3);
    setAwake(true);
    timeout.current = setTimeout(settle, AWAKENING_MS);
  }, [compact, reducedMotion, settle]);

  useEffect(() => {
    const preference = window.matchMedia?.('(prefers-reduced-motion: reduce)');
    const update = () => setReducedMotion(preference ? preference.matches : true);
    update();
    preference?.addEventListener?.('change', update);
    return () => preference?.removeEventListener?.('change', update);
  }, []);

  useEffect(() => {
    if (compact || reducedMotion) {
      settle();
      return undefined;
    }

    // A linked logo uses its existing link for keyboard access. Standalone
    // artwork has its own replay control, never nested inside another control.
    const owner = element.current.parentElement?.closest('a, button, [role="button"], [role="link"]');
    setStandalone(!owner);
    owner?.addEventListener('focus', awaken);
    const onVisibility = () => { if (document.hidden) settle(); };
    document.addEventListener('visibilitychange', onVisibility);

    let observer;
    if ('IntersectionObserver' in window) {
      observer = new IntersectionObserver(entries => {
        if (entries.some(entry => entry.isIntersecting)) {
          awaken();
          observer.disconnect();
        }
      }, { threshold: 0.5 });
      observer.observe(element.current);
    } else {
      awaken();
    }

    return () => {
      observer?.disconnect();
      owner?.removeEventListener('focus', awaken);
      document.removeEventListener('visibilitychange', onVisibility);
      clearTimeout(timeout.current);
      playing.current = false;
    };
  }, [awaken, compact, reducedMotion, settle]);

  return (
    <span
      ref={element}
      className={`nm-brand nm-brand-living ${compact ? 'nm-brand-compact' : ''}`}
      data-tone={tone}
      data-awake={awake ? 'true' : 'false'}
      data-palette={palette}
      onPointerEnter={awaken}
      onPointerDown={awaken}
    >
      <span className="nm-brand-scene">
        <span className="nm-brand-cosmos" aria-hidden="true">
          <span className="nm-brand-halo" />
          <span className="nm-brand-orbit nm-brand-orbit-a"><span className="nm-brand-orbit-track" /><span className="nm-brand-traveller"><span className="nm-brand-planet" /></span></span>
          <span className="nm-brand-orbit nm-brand-orbit-b"><span className="nm-brand-orbit-track" /><span className="nm-brand-traveller"><span className="nm-brand-planet" /></span></span>
          <span className="nm-brand-orbit nm-brand-orbit-c"><span className="nm-brand-traveller"><span className="nm-brand-planet" /></span></span>
        </span>
        <span className="nm-brand-art" role="img" aria-label={NAME}>
          <img className="nm-brand-logo nm-brand-logo-light" src={`${process.env.PUBLIC_URL}/images/brand/numerom-logo.svg`} width="995" height="785" alt="" aria-hidden="true" />
          <img className="nm-brand-logo nm-brand-logo-dark" src={`${process.env.PUBLIC_URL}/images/brand/numerom-logo-dark.svg`} width="995" height="785" alt="" aria-hidden="true" />
          <span className="nm-brand-heart" aria-hidden="true" />
        </span>
      </span>
      {standalone && !compact && !reducedMotion && (
        <button className="nm-brand-replay" type="button" aria-label="Оживить логотип NumerOM" title="Оживить логотип" onClick={awaken} />
      )}
    </span>
  );
};
