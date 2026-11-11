function relationshipVoice(score){
 if(!Number.isInteger(score)||score<1||score>10)return null;
 return 'relationship-'+(score===10?'same':score>=8?'close':score>=6?'different':'contrast');
}
module.exports={relationshipVoice};
