import React, { memo, useCallback, useEffect, useId, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, AppState, Easing, Pressable, StyleSheet, View } from 'react-native';
import Svg, { Circle, Defs, RadialGradient, Stop, SvgXml } from 'react-native-svg';
import { logoLight, logoDark, logoAspectRatio } from '../../assets/brand/logo.generated';

const PALETTES = [
  ['#7ccfb8', '#7a9fdf', '#b7a2d7'],
  ['#67c6cb', '#aaa2e4', '#d6b37d'],
  ['#9ac99c', '#80b7d8', '#cd9dbc'],
] as const;
const ORBITS = [
  { angle: '-28deg', tilt: '61deg', reverseTilt: '-61deg', start: '12deg', end: '332deg', size: .08 },
  { angle: '37deg', tilt: '55deg', reverseTilt: '-55deg', start: '170deg', end: '-110deg', size: .06 },
  { angle: '-11deg', tilt: '18deg', reverseTilt: '-18deg', start: '245deg', end: '485deg', size: .045 },
];
const NAME = 'NumerOM — Numbers Reveal';

// SvgXml parses once per artwork/tone change; animation only transforms Views.
const Artwork = memo(({ tone }: { tone: 'light' | 'dark' }) => (
  <SvgXml xml={tone === 'dark' ? logoDark : logoLight} width="100%" height="100%" accessible={false} />
));
const Planet = memo(({ color, size }: { color: string; size: number }) => {
  const gradient = useId().replace(/:/g, '');
  return <Svg width={size} height={size} viewBox="0 0 100 100" accessible={false}>
    <Defs><RadialGradient id={gradient} cx="28%" cy="25%" rx="80%" ry="80%">
      <Stop offset="0" stopColor="#f4fffa" /><Stop offset=".45" stopColor={color} /><Stop offset="1" stopColor="#405867" />
    </RadialGradient></Defs>
    <Circle cx="50" cy="50" r="49" fill={`url(#${gradient})`} />
  </Svg>;
});

export function Brand({ compact = false, tone = 'light' }: { compact?: boolean; tone?: 'light' | 'dark' }) {
  const width = compact ? 104 : 146;
  const height = width / logoAspectRatio;
  const diameter = width * .742;
  const progress = useRef(new Animated.Value(0)).current;
  const animation = useRef<Animated.CompositeAnimation | null>(null);
  const playing = useRef(false);
  const sequence = useRef(0);
  // Be still until the device's accessibility preference is known.
  const [reducedMotion, setReducedMotion] = useState(true);
  const [palette, setPalette] = useState(0);

  const settle = useCallback(() => {
    animation.current?.stop();
    progress.setValue(0);
    playing.current = false;
  }, [progress]);

  const awaken = useCallback(() => {
    if (compact || reducedMotion || playing.current || (AppState.currentState && AppState.currentState !== 'active')) return;
    playing.current = true;
    setPalette(sequence.current++ % PALETTES.length);
    progress.setValue(0);
    animation.current = Animated.timing(progress, {
      toValue: 1,
      duration: 4400,
      easing: Easing.inOut(Easing.cubic),
      useNativeDriver: true,
      isInteraction: false,
    });
    animation.current.start(() => { playing.current = false; });
  }, [compact, progress, reducedMotion]);

  useEffect(() => {
    let mounted = true;
    let preferenceChanged = false;
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', value => {
      preferenceChanged = true;
      if (mounted) setReducedMotion(value);
    });
    AccessibilityInfo.isReduceMotionEnabled().then(value => {
      if (mounted && !preferenceChanged) setReducedMotion(value);
    }).catch(() => { /* Keep the static artwork when preferences are unavailable. */ });
    return () => { mounted = false; subscription.remove(); };
  }, []);

  useEffect(() => {
    awaken();
    const subscription = AppState.addEventListener('change', state => { if (state !== 'active') settle(); });
    return () => { subscription.remove(); settle(); };
  }, [awaken, settle]);

  const opacity = progress.interpolate({ inputRange: [0, .13, .35, .7, 1], outputRange: [0, .85, 1, 1, 0] });
  const sphereOpacity = progress.interpolate({ inputRange: [0, .24, .7, 1], outputRange: [0, .9, .9, 0] });
  const content = <Animated.View pointerEvents="none" accessible={false} style={[StyleSheet.absoluteFill, {
    transform: [
      { perspective: 600 },
      { rotateX: progress.interpolate({ inputRange: [0, .23, .6, .85, 1], outputRange: ['0deg', '5deg', '-3deg', '1deg', '0deg'] }) },
      { rotateY: progress.interpolate({ inputRange: [0, .23, .6, .85, 1], outputRange: ['0deg', '-11deg', '8deg', '-2deg', '0deg'] }) },
      { rotateZ: progress.interpolate({ inputRange: [0, .23, .6, 1], outputRange: ['0deg', '-1deg', '.6deg', '0deg'] }) },
    ],
  }]}>
    <Animated.View style={[StyleSheet.absoluteFill, { opacity }]}>
      {ORBITS.map((orbit, index) => {
        const size = diameter * orbit.size;
        return <View key={index} style={{ position: 'absolute', left: width * .025, top: height * .03, width: diameter, height: diameter,
          transform: [{ perspective: 600 }, { rotateZ: orbit.angle }, { rotateX: orbit.tilt }] }}>
          {index < 2 && <View style={[StyleSheet.absoluteFill, { borderRadius: diameter / 2, borderWidth: .65, borderColor: PALETTES[palette][index], opacity: .33 }]} />}
          <Animated.View style={[StyleSheet.absoluteFill, { transform: [{ rotateZ: progress.interpolate({ inputRange: [0, 1], outputRange: [orbit.start, orbit.end] }) }] }]}>
            <View style={{ position: 'absolute', left: diameter / 2 - size / 2, top: -size / 2, transform: [{ rotateX: orbit.reverseTilt }] }}>
              <Planet color={PALETTES[palette][index]} size={size} />
            </View>
          </Animated.View>
        </View>;
      })}
    </Animated.View>
    <Artwork tone={tone} />
    <Animated.View style={{ position: 'absolute', left: width * (.7638 - .1407 / 2), top: height * .4994 - width * .1407 / 2, opacity: sphereOpacity }}>
      <Planet color={PALETTES[palette][0]} size={width * .1407} />
    </Animated.View>
  </Animated.View>;

  if (compact || reducedMotion) {
    return <View accessible accessibilityRole="image" accessibilityLabel={NAME} style={{ width, height }}>
      <Artwork tone={tone} />
    </View>;
  }
  return <Pressable accessibilityRole="button" accessibilityLabel={NAME} accessibilityHint="Повторить анимацию орбит и планет" onPress={awaken} style={{ width, height }}>
    {content}
  </Pressable>;
}
