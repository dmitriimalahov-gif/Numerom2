const amount = value => Number.isFinite(value) && value >= 0;

// One notice per session, shared by local checks and server refusals.
function createCreditNotice() {
 let owner = null, balance, notice = null;
 const listeners = new Set();
 const publish = next => {
  if (notice === next) return;
  notice = next;
  listeners.forEach(listener => listener());
 };
 const dismiss = () => publish(null);
 const show = details => {
  if (!owner || notice) return;
  publish({...details});
 };
 return {
  getSnapshot: () => notice,
  subscribe: listener => {listeners.add(listener); return () => listeners.delete(listener);},
  dismiss,
  sync(nextOwner, nextBalance) {
   if (nextOwner !== owner) {
    owner = nextOwner; balance = nextBalance; dismiss(); return;
   }
   const previous = balance;
   balance = nextBalance;
   if (!owner) return;
   if (amount(previous) && previous > 0 && nextBalance === 0) show({balance:0});
   // A confirmed top-up/reward clears an obsolete notice.
   if (notice && amount(previous) && nextBalance > previous &&
       (notice.cost === undefined || nextBalance >= notice.cost)) dismiss();
  },
  insufficient(details) {
   if (amount(details.balance) && amount(details.cost) && details.balance < details.cost) show(details);
  },
  serverRefused(requestOwner) {
   // A late response from a previous account must never interrupt the new one.
   if (requestOwner === owner) show({});
  },
 };
}

function creditNoticeText(notice) {
 const empty = notice.balance === 0;
 const details = amount(notice.balance) && amount(notice.cost)
  ? `На балансе: ${notice.balance} балл. Для этого действия нужно: ${notice.cost} балл.`
  : 'Выберите пакет пополнения, чтобы продолжить расчёты.';
 return {
  title: empty ? 'У вас закончились баллы' : 'Недостаточно баллов',
  description: details,
 };
}
module.exports = {createCreditNotice, creditNoticeText};
