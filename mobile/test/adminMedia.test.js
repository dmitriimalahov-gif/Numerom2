const test=require('node:test');const assert=require('node:assert/strict');
const {attachmentUrl,materialUrl,consultationUrl}=require('../src/features/admin/mediaUrl');
test('review attachments open only private same-origin media endpoint',()=>{
 const base='https://api.example.test';const path='/api/student/exercise-attachment-media/signed-token';
 assert.equal(attachmentUrl(base+path,base),base+path);
 for(const value of ['https://other.test'+path,'javascript:alert(1)',base+'/uploads/test.pdf','http://api.example.test'+path,'https://u:p@api.example.test'+path,base+path+'/file'])assert.throws(()=>attachmentUrl(value,base));
});
test('lesson material access is distinct from submitted exercise files',()=>{
 const base='https://api.example.test',path='/api/student/media/signed-token';
 assert.equal(materialUrl(base+path,base),base+path);
 assert.throws(()=>attachmentUrl(base+path,base));
 for(const value of [base+'/api/student/exercise-attachment-media/test',base+'/uploads/lesson.pdf',base+path+'/extra','https://other.test'+path])assert.throws(()=>materialUrl(value,base));
});
test('only local QA supports plain HTTP attachment access',()=>{
 const path='/api/student/exercise-attachment-media/test';
 assert.equal(attachmentUrl('http://127.0.0.1:8014'+path,'http://127.0.0.1:8014'),'http://127.0.0.1:8014'+path);
 assert.throws(()=>attachmentUrl('http://remote.test'+path,'http://remote.test'));
});
test('consultation preview uses only the same-origin signed consultation route',()=>{
 const base='https://api.example.test',path='/api/student/consultation-media/token';
 assert.equal(consultationUrl(base+path,base),base+path);
 assert.throws(()=>consultationUrl(base+'/api/student/media/token',base));
 assert.throws(()=>consultationUrl('https://other.test'+path,base));
});
