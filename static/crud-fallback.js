(function(){
  const qs=(s)=>document.querySelector(s);
  async function api(url,opts={}){
    const res=await fetch(url,{cache:"no-store",headers:{"Content-Type":"application/json",...(opts.headers||{})},...opts});
    const data=await res.json().catch(()=>({}));
    if(!res.ok) throw new Error(data.error||("Request failed ("+res.status+")"));
    return data;
  }
  function result(kind,msg,ok){
    const el=qs("#"+kind+"-result");
    if(el){el.innerHTML=(ok?"<b>Saved.</b> ":"<b>Save failed.</b> ")+msg;}
  }
  document.addEventListener("click",async function(e){
    const et=e.target.closest("[data-edit-timetable],[data-edit-progress]");
    if(!et)return;
    e.preventDefault(); e.stopImmediatePropagation();
    try{
      if(et.hasAttribute("data-edit-timetable")){
        const id=et.getAttribute("data-edit-timetable");
        const rows=await api("/api/timetable");
        const row=(rows||[]).find(x=>String(x.id)===String(id));
        const f=qs('[data-op-form="timetable"]');
        if(!row||!f)throw new Error("Could not find that timetable row.");
        const rooms=await api("/api/rooms"), subjects=await api("/api/subjects");
        f.elements.editing_id.value=row.id;
        f.elements.day.value=row.day||"Monday";
        f.elements.start_time.value=String(row.start_time||"").slice(0,5);
        f.elements.end_time.value=String(row.end_time||"").slice(0,5);
        f.elements.section.value=row.section||"";
        f.elements.room.innerHTML=(rooms||[]).map(x=>'<option value="'+String(x.room_number).replace(/"/g,"&quot;")+'">'+x.room_number+" · "+x.room_name+"</option>").join("");
        f.elements.subject.innerHTML=(subjects||[]).map(x=>'<option value="'+String(x.code).replace(/"/g,"&quot;")+'">'+x.code+" · "+x.name+"</option>").join("");
        f.elements.room.value=row.rooms?.room_number||"";
        f.elements.subject.value=row.subjects?.code||"";
        const b=f.querySelector('[data-timetable-submit]'); if(b)b.textContent="◫ Update clash-free entry";
        result("timetable","Editing the selected row.",true);
      }else{
        const id=et.getAttribute("data-edit-progress");
        const rows=await api("/api/progress");
        const row=(rows||[]).find(x=>String(x.id)===String(id));
        const f=qs('[data-op-form="progress"]');
        if(!row||!f)throw new Error("Could not find that syllabus row.");
        const subjects=await api("/api/subjects");
        f.elements.editing_id.value=row.id;
        f.elements.code.innerHTML=(subjects||[]).map(x=>'<option value="'+String(x.code).replace(/"/g,"&quot;")+'">'+x.code+" · "+x.name+"</option>").join("");
        f.elements.code.value=row.subjects?.code||"";
        f.elements.week_number.value=row.week_number;
        f.elements.coverage_percent.value=row.coverage_percent;
        f.elements.topics_covered.value=row.topics_covered||"";
        if(f.elements.credits)f.elements.credits.value=row.subjects?.credits||"";
        const b=f.querySelector('[data-progress-submit]'); if(b)b.textContent="⌁ Update syllabus entry";
        result("progress","Editing the selected row.",true);
      }
    }catch(err){result(et.hasAttribute("data-edit-timetable")?"timetable":"progress",err.message,false);}
  },true);

  document.addEventListener("submit",async function(e){
    const f=e.target.closest('[data-op-form="timetable"],[data-op-form="progress"]');
    if(!f)return;
    e.preventDefault(); e.stopImmediatePropagation();
    const kind=f.dataset.op, data=Object.fromEntries(new FormData(f));
    const button=f.querySelector('button[type="submit"]');
    if(button){button.disabled=true;button.textContent="Saving…";}
    try{
      if(kind==="timetable"){
        const [rooms,subjects]=await Promise.all([api("/api/rooms"),api("/api/subjects")]);
        const room=(rooms||[]).find(x=>String(x.room_number).trim().toLowerCase()===String(data.room).trim().toLowerCase());
        const subject=(subjects||[]).find(x=>String(x.code).trim().toLowerCase()===String(data.subject).trim().toLowerCase());
        if(!room)throw new Error("Room not found in the live database.");
        if(!subject)throw new Error("Subject not found in the live database.");
        const dayOrder={Monday:1,Tuesday:2,Wednesday:3,Thursday:4,Friday:5,Saturday:6};
        const payload={day:data.day,day_order:dayOrder[data.day],start_time:data.start_time,end_time:data.end_time,room_id:room.id,section:data.section,subject_id:subject.id};
        if(data.editing_id)await api("/api/timetable/"+encodeURIComponent(data.editing_id),{method:"PATCH",body:JSON.stringify(payload)});
        else await api("/api/timetable",{method:"POST",body:JSON.stringify(payload)});
        result("timetable",data.editing_id?"Timetable row updated in Supabase.":"Timetable row created in Supabase.",true);
      }else{
        const subjects=await api("/api/subjects");
        const subject=(subjects||[]).find(x=>String(x.code).trim().toLowerCase()===String(data.code).trim().toLowerCase());
        if(!subject)throw new Error("Subject not found in the live database.");
        const payload={subject_id:subject.id,week_number:Number(data.week_number),coverage_percent:Number(data.coverage_percent),topics_covered:data.topics_covered};
        if(data.editing_id)await api("/api/progress/"+encodeURIComponent(data.editing_id),{method:"PATCH",body:JSON.stringify(payload)});
        else await api("/api/progress",{method:"POST",body:JSON.stringify(payload)});
        result("progress",data.editing_id?"Syllabus row updated in Supabase.":"Syllabus row created in Supabase.",true);
      }
      f.elements.editing_id.value="";
      setTimeout(()=>location.reload(),500);
    }catch(err){result(kind,err.message,false);}
    finally{if(button){button.disabled=false;}}
  },true);
})();