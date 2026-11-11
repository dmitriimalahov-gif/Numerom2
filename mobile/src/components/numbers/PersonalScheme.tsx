import {Pressable, StyleSheet, Text, View} from 'react-native';
import {NumberDetailView} from '../../lib/personalReport';
import {PersonalSchemeView, SchemeCell, SchemeLine} from '../../lib/personalScheme';

const INK = '#003447';
const MINT = '#E8F4EE';
const HIGHLIGHT = '#CBE6DA';
const DIGIT_COLORS: Record<number,string> = {1:'#F47758',2:'#FFFFFF',3:'#FA9418',4:'#BA9669',5:'#BEDFD0',6:'#F8CBD3',7:'#BCBFC0',8:'#3867AD',9:'#F53F58'};
const ROWS = [[1,4,7],[2,5,8],[3,6,9]];
const TOP = ['soul','mind','destiny'];
const LABELS: Record<string,string> = {soul:'ч/д',mind:'ч/у',destiny:'ч/с',helping_mind:'ч/у*',wisdom:'ч/м',ruling:'п/ч',full_name:'Имя'};

export function PersonalScheme({numbers,scheme,selected,onNumber,onCell,onLine}: {
  numbers:NumberDetailView[]; scheme:PersonalSchemeView|null; selected:string;
  onNumber:(item:NumberDetailView)=>void; onCell:(item:SchemeCell)=>void; onLine:(item:SchemeLine)=>void;
}) {
  const activeLine = scheme?.lines.find(line => `line-${line.key}` === selected);
  const personal = (key:string,wide=false) => {
    const item = numbers.find(number => number.key === key);
    if (!item) return <View key={key} style={styles.cell}/>;
    return <Pressable key={key} accessibilityRole="button" accessibilityLabel={`${item.title}: ${item.value ?? 'нет значения'}. Открыть расшифровку`}
      accessibilityHint="Откроется пояснение и формула. Баллы не списываются."
      accessibilityState={{selected:selected===key}} onPress={() => onNumber(item)}
      style={({pressed}) => [styles.cell,styles.personal,wide && styles.widePersonal,selected===key && styles.selected,pressed && styles.pressed]}>
      <Text style={styles.code}>{LABELS[key]}</Text><Text style={styles.number}>{item.value ?? '—'}</Text>
    </Pressable>;
  };
  const line = (key:string,label:string) => {
    const item = scheme?.lines.find(candidate => candidate.key === key);
    return item ? <Pressable key={key} accessibilityRole="button" accessibilityLabel={`${item.title}: ${item.value}. Открыть расшифровку`}
      accessibilityState={{selected:selected===`line-${key}`}} onPress={() => onLine(item)}
      style={({pressed}) => [styles.cell,styles.line,selected===`line-${key}` && styles.selected,pressed && styles.pressed]}>
      <Text style={styles.number}>{item.value}</Text><Text style={styles.lineLabel}>{label}</Text>
    </Pressable> : <View key={key} style={styles.cell}><Text style={styles.number}>—</Text></View>;
  };
  return <View style={styles.scheme}>
    <Text style={styles.instruction}>Нажмите на ячейку — откроется расшифровка.</Text>
    {scheme ? <View accessibilityLabel="Персональная схема NumerOM" style={styles.grid}>
      {ROWS.map((digits,row) => <View key={row} style={styles.row}>
        {personal(TOP[row])}
        {digits.map(digit => {
          const item = scheme.cells.find(cell => cell.digit === digit)!;
          const chosen = selected === `cell-${digit}`;
          const highlighted = chosen || !!activeLine?.digits.includes(digit);
          const dark = highlighted && digit === 8;
          return <Pressable key={digit} accessibilityRole="button" accessibilityLabel={`${item.title}. Количество: ${item.count}. Открыть расшифровку`}
            accessibilityState={{selected:chosen}} onPress={() => onCell(item)}
            style={({pressed}) => [styles.cell,highlighted && {backgroundColor:DIGIT_COLORS[digit],borderColor:INK},pressed && styles.pressed]}>
            <Text style={[styles.number,dark && styles.white]}>{item.count}</Text>
            <View style={styles.digitLabel}><View style={[styles.dot,{backgroundColor:DIGIT_COLORS[digit]}]}/><Text style={[styles.code,dark && styles.white]}>{digit}</Text></View>
          </Pressable>;
        })}
        {line(`row-${row}`,'→')}
      </View>)}
      <View style={styles.row}>
        {line('diag-1','3·5·7')}{[0,1,2].map(col => line(`col-${col}`,'↓'))}{line('diag-0','1·5·9')}
      </View>
    </View> : <View style={styles.row}>{TOP.map(key => personal(key))}</View>}
    <View style={styles.row}>{['helping_mind','wisdom','ruling'].map(key => personal(key,true))}</View>
    <View style={styles.nameRow}>
      <Text style={styles.legend}>ч/д — душа · ч/у — ум · ч/с — судьба{`\n`}ч/у* — помощь уму · ч/м — мудрость{`\n`}п/ч — правящее число</Text>
      {personal('full_name')}
    </View>
    <Text style={styles.legend}>{scheme ? 'В центре — количество цифр 1–9. Справа и снизу — суммы по линиям.' : 'Квадрат для этого результата пока не получен. Личные числа доступны выше.'}</Text>
  </View>;
}

const styles = StyleSheet.create({
  scheme:{gap:9},instruction:{fontSize:13,lineHeight:20,color:'#61758B',marginBottom:6},grid:{gap:7},row:{flexDirection:'row',gap:7},
  cell:{flex:1,minWidth:0,minHeight:60,aspectRatio:1,maxHeight:96,backgroundColor:MINT,borderRadius:15,borderWidth:1.5,borderColor:'transparent',alignItems:'center',justifyContent:'center',gap:3,paddingVertical:6},
  personal:{backgroundColor:'#DDEEE5'},widePersonal:{aspectRatio:undefined,minHeight:66,flexDirection:'row',gap:12},
  selected:{backgroundColor:HIGHLIGHT,borderColor:INK},pressed:{opacity:.72},line:{backgroundColor:'#F0F7F3'},
  number:{fontSize:28,lineHeight:32,color:INK,fontWeight:'500',fontVariant:['tabular-nums']},code:{fontSize:12,lineHeight:17,color:INK,fontWeight:'500'},
  lineLabel:{fontSize:11,lineHeight:15,color:'#4A685C'},digitLabel:{flexDirection:'row',alignItems:'center',gap:4},dot:{width:7,height:7,borderRadius:4,borderWidth:.5,borderColor:'#426055'},
  nameRow:{flexDirection:'row',alignItems:'center',gap:12,marginTop:5},legend:{flexShrink:1,fontSize:11,lineHeight:18,color:'#536D63'},white:{color:'#FFFFFF'},
});
