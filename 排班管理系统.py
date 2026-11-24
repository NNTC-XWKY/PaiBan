# -*- coding: utf-8 -*-
"""
餐饮/酒店排班管理系统 MVP
Windows 桌面版；Python 3.10+；仅使用标准库。
"""
import csv, json, random, sys
from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# 打包为 EXE 后，数据文件保存在 EXE 同目录，避免写入临时解压目录
APP_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "schedule_data.json")

DEFAULT_SHIFTS = [
    {"name": "早班", "start": "07:00", "end": "15:00", "mode": "两班/三班通用", "min": 2, "max": 8},
    {"name": "中班", "start": "15:00", "end": "23:00", "mode": "三班制", "min": 2, "max": 8},
    {"name": "夜班", "start": "23:00", "end": "07:00", "mode": "两班/三班通用", "min": 2, "max": 8},
]
DEFAULT_DATA = {"employees": [], "shifts": DEFAULT_SHIFTS, "assignments": [], "settings": {"rest_hours": 11}}

class RosterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("餐饮 / 酒店智能排班管理系统")
        self.root.geometry("1180x760")
        self.root.minsize(980, 620)
        self.data = self.load_data()
        self.build_ui()
        self.refresh_all()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    d = json.load(f)
                for k, v in DEFAULT_DATA.items():
                    d.setdefault(k, v)
                return d
            except Exception:
                pass
        return json.loads(json.dumps(DEFAULT_DATA, ensure_ascii=False))

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def build_ui(self):
        top = ttk.Frame(self.root, padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="智能排班管理系统", font=("Microsoft YaHei UI", 18, "bold")).pack(side="left")
        ttk.Label(top, text="餐饮 / 酒店 · 20–50人 · 两班倒 / 三班倒", foreground="#555").pack(side="left", padx=18)
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self.roster_tab = ttk.Frame(self.tabs, padding=10)
        self.staff_tab = ttk.Frame(self.tabs, padding=10)
        self.shift_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.roster_tab, text="排班表")
        self.tabs.add(self.staff_tab, text="员工管理")
        self.tabs.add(self.shift_tab, text="班次设置")
        self.build_roster()
        self.build_staff()
        self.build_shifts()

    def build_roster(self):
        bar = ttk.Frame(self.roster_tab)
        bar.pack(fill="x", pady=(0,8))
        ttk.Label(bar, text="开始日期 (YYYY-MM-DD)：").pack(side="left")
        self.start_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(bar, textvariable=self.start_var, width=13).pack(side="left", padx=(0,12))
        ttk.Label(bar, text="排班天数：").pack(side="left")
        self.days_var = tk.StringVar(value="7")
        ttk.Combobox(bar, textvariable=self.days_var, values=["7","14","28","30","31"], width=5, state="readonly").pack(side="left", padx=(0,12))
        ttk.Label(bar, text="排班模式：").pack(side="left")
        self.mode_var = tk.StringVar(value="三班倒")
        ttk.Combobox(bar, textvariable=self.mode_var, values=["两班倒","三班倒"], width=9, state="readonly").pack(side="left", padx=(0,12))
        ttk.Button(bar, text="自动生成排班", command=self.auto_schedule).pack(side="left", padx=4)
        ttk.Button(bar, text="手动调整选中项", command=self.edit_assignment).pack(side="left", padx=4)
        ttk.Button(bar, text="删除选中项", command=self.delete_assignment).pack(side="left", padx=4)
        ttk.Button(bar, text="导出 Excel可打开CSV", command=self.export_csv).pack(side="right", padx=4)

        hint = ttk.Label(self.roster_tab, text="提示：双击排班记录可修改员工、日期和班次。自动排班会尽量均衡工时，并避免员工连续跨班；生成新排班前会替换所选日期范围内的旧排班。", foreground="#555")
        hint.pack(anchor="w", pady=(0,8))
        cols = ("date","weekday","shift","time","employee","role")
        self.roster = ttk.Treeview(self.roster_tab, columns=cols, show="headings", height=23)
        titles = {"date":"日期","weekday":"星期","shift":"班次","time":"时间","employee":"员工","role":"岗位"}
        widths = {"date":120,"weekday":75,"shift":100,"time":130,"employee":150,"role":130}
        for c in cols:
            self.roster.heading(c, text=titles[c]); self.roster.column(c, width=widths[c], anchor="center")
        self.roster.pack(fill="both", expand=True)
        self.roster.bind("<Double-1>", lambda e: self.edit_assignment())

    def build_staff(self):
        form = ttk.LabelFrame(self.staff_tab, text="新增 / 编辑员工", padding=10)
        form.pack(fill="x", pady=(0,10))
        self.staff_name = tk.StringVar()
        self.staff_role = tk.StringVar(value="服务员")
        self.staff_type = tk.StringVar(value="全职")
        self.staff_active = tk.BooleanVar(value=True)
        for label, var, width in [("姓名",self.staff_name,14),("岗位",self.staff_role,14),("用工类型",self.staff_type,12)]:
            ttk.Label(form, text=label).pack(side="left", padx=(0,4))
            ttk.Entry(form, textvariable=var, width=width).pack(side="left", padx=(0,12))
        ttk.Checkbutton(form, text="在职", variable=self.staff_active).pack(side="left", padx=4)
        ttk.Button(form, text="添加员工", command=self.add_employee).pack(side="left", padx=8)
        ttk.Button(form, text="更新选中员工", command=self.update_employee).pack(side="left", padx=4)
        ttk.Button(form, text="删除选中员工", command=self.delete_employee).pack(side="left", padx=4)
        self.staff_tree = ttk.Treeview(self.staff_tab, columns=("name","role","type","active"), show="headings", height=22)
        for c,t,w in [("name","姓名",180),("role","岗位",180),("type","用工类型",140),("active","状态",100)]:
            self.staff_tree.heading(c,text=t); self.staff_tree.column(c,width=w,anchor="center")
        self.staff_tree.pack(fill="both",expand=True)
        self.staff_tree.bind("<<TreeviewSelect>>", self.on_staff_select)

    def build_shifts(self):
        ttk.Label(self.shift_tab, text="可按门店实际情况调整班次时间及每班最低 / 最高人数。两班倒默认使用早班、夜班；三班倒使用早班、中班、夜班。", wraplength=900).pack(anchor="w", pady=(0,10))
        self.shift_tree = ttk.Treeview(self.shift_tab, columns=("name","start","end","min","max"), show="headings", height=14)
        for c,t,w in [("name","班次名称",180),("start","开始时间",150),("end","结束时间",150),("min","最低人数",120),("max","最高人数",120)]:
            self.shift_tree.heading(c,text=t); self.shift_tree.column(c,width=w,anchor="center")
        self.shift_tree.pack(fill="x")
        form = ttk.LabelFrame(self.shift_tab, text="编辑班次", padding=10)
        form.pack(fill="x", pady=12)
        self.sh_name=tk.StringVar(); self.sh_start=tk.StringVar(); self.sh_end=tk.StringVar()
        self.sh_min=tk.StringVar(value="2"); self.sh_max=tk.StringVar(value="8")
        for label,var,w in [("名称",self.sh_name,12),("开始",self.sh_start,9),("结束",self.sh_end,9),("最低人数",self.sh_min,5),("最高人数",self.sh_max,5)]:
            ttk.Label(form,text=label).pack(side="left",padx=(0,4))
            ttk.Entry(form,textvariable=var,width=w).pack(side="left",padx=(0,12))
        ttk.Button(form,text="新增班次",command=self.add_shift).pack(side="left",padx=4)
        ttk.Button(form,text="更新选中班次",command=self.update_shift).pack(side="left",padx=4)
        ttk.Button(form,text="删除选中班次",command=self.delete_shift).pack(side="left",padx=4)
        self.shift_tree.bind("<<TreeviewSelect>>",self.on_shift_select)

    def refresh_all(self):
        self.refresh_staff(); self.refresh_shifts(); self.refresh_roster()

    def refresh_staff(self):
        self.staff_tree.delete(*self.staff_tree.get_children())
        for e in self.data["employees"]:
            self.staff_tree.insert("", "end", iid=e["id"], values=(e["name"],e["role"],e["type"],"在职" if e["active"] else "停用"))

    def refresh_shifts(self):
        self.shift_tree.delete(*self.shift_tree.get_children())
        for s in self.data["shifts"]:
            self.shift_tree.insert("", "end", iid=s["name"], values=(s["name"],s["start"],s["end"],s["min"],s["max"]))

    def refresh_roster(self):
        self.roster.delete(*self.roster.get_children())
        emap={e["id"]:e for e in self.data["employees"]}
        for i,a in enumerate(sorted(self.data["assignments"],key=lambda x:(x["date"],x["shift"],x["employee_id"]))):
            e=emap.get(a["employee_id"],{})
            try: wd=["周一","周二","周三","周四","周五","周六","周日"][date.fromisoformat(a["date"]).weekday()]
            except: wd=""
            self.roster.insert("", "end", iid=str(i), values=(a["date"],wd,a["shift"],a["time"],e.get("name","[员工已删除]"),e.get("role","")))

    def add_employee(self):
        name=self.staff_name.get().strip()
        if not name: messagebox.showwarning("提示","请输入员工姓名"); return
        if any(e["name"]==name for e in self.data["employees"]): messagebox.showwarning("提示","员工姓名已存在"); return
        self.data["employees"].append({"id":str(int(datetime.now().timestamp()*1000000)),"name":name,"role":self.staff_role.get().strip() or "未设置","type":self.staff_type.get().strip() or "全职","active":self.staff_active.get()})
        self.save(); self.refresh_all(); self.staff_name.set("")

    def selected_staff(self):
        sel=self.staff_tree.selection()
        if not sel: return None
        return next((e for e in self.data["employees"] if e["id"]==sel[0]),None)

    def on_staff_select(self,_=None):
        e=self.selected_staff()
        if e:
            self.staff_name.set(e["name"]); self.staff_role.set(e["role"]); self.staff_type.set(e["type"]); self.staff_active.set(e["active"])

    def update_employee(self):
        e=self.selected_staff()
        if not e: messagebox.showinfo("提示","请先选择员工"); return
        name=self.staff_name.get().strip()
        if not name: messagebox.showwarning("提示","姓名不能为空"); return
        e.update(name=name,role=self.staff_role.get().strip(),type=self.staff_type.get().strip(),active=self.staff_active.get())
        self.save(); self.refresh_all()

    def delete_employee(self):
        e=self.selected_staff()
        if not e: return
        if messagebox.askyesno("确认",f"删除员工 {e['name']}？历史排班记录会保留。"):
            self.data["employees"].remove(e); self.save(); self.refresh_all()

    def selected_shift(self):
        sel=self.shift_tree.selection()
        if not sel:return None
        return next((s for s in self.data["shifts"] if s["name"]==sel[0]),None)

    def on_shift_select(self,_=None):
        s=self.selected_shift()
        if s:
            self.sh_name.set(s["name"]);self.sh_start.set(s["start"]);self.sh_end.set(s["end"]);self.sh_min.set(str(s["min"]));self.sh_max.set(str(s["max"]))

    def add_shift(self):
        try:
            s={"name":self.sh_name.get().strip(),"start":self.sh_start.get().strip(),"end":self.sh_end.get().strip(),"min":int(self.sh_min.get()),"max":int(self.sh_max.get())}
            datetime.strptime(s["start"],"%H:%M");datetime.strptime(s["end"],"%H:%M")
            if not s["name"] or s["min"]<0 or s["max"]<s["min"]: raise ValueError()
            if any(x["name"]==s["name"] for x in self.data["shifts"]): raise ValueError()
        except: messagebox.showerror("输入错误","请检查班次名称、时间及人数范围（时间格式 HH:MM）。");return
        self.data["shifts"].append(s);self.save();self.refresh_all()

    def update_shift(self):
        s=self.selected_shift()
        if not s: messagebox.showinfo("提示","请先选择班次");return
        old=s["name"]
        try:
            new={"name":self.sh_name.get().strip(),"start":self.sh_start.get().strip(),"end":self.sh_end.get().strip(),"min":int(self.sh_min.get()),"max":int(self.sh_max.get())}
            datetime.strptime(new["start"],"%H:%M");datetime.strptime(new["end"],"%H:%M")
            if not new["name"] or new["min"]<0 or new["max"]<new["min"]:raise ValueError()
        except:messagebox.showerror("输入错误","请检查班次设置。");return
        s.update(new)
        for a in self.data["assignments"]:
            if a["shift"]==old:
                a["shift"]=new["name"];a["time"]=new["start"]+"-"+new["end"]
        self.save();self.refresh_all()

    def delete_shift(self):
        s=self.selected_shift()
        if not s:return
        if any(a["shift"]==s["name"] for a in self.data["assignments"]):
            messagebox.showwarning("无法删除","该班次已有排班记录，请先删除或调整相关排班。");return
        self.data["shifts"].remove(s);self.save();self.refresh_all()

    def active_shifts(self):
        mode=self.mode_var.get()
        shifts=self.data["shifts"]
        if mode=="两班倒":
            chosen=[s for s in shifts if s["name"] in ("早班","夜班")]
            return chosen if len(chosen)>=2 else shifts[:2]
        return shifts[:3]

    def auto_schedule(self):
        try:
            start=date.fromisoformat(self.start_var.get().strip()); days=int(self.days_var.get())
        except:messagebox.showerror("日期错误","请输入正确开始日期，格式 YYYY-MM-DD。");return
        staff=[e for e in self.data["employees"] if e["active"]]
        if not staff:messagebox.showwarning("缺少员工","请先在员工管理中添加在职员工。");return
        shifts=self.active_shifts()
        if len(shifts)<2:messagebox.showwarning("班次不足","请至少设置两个班次。");return
        if not messagebox.askyesno("确认生成",f"将生成 {start} 起 {days} 天的{self.mode_var.get()}排班，并替换该日期范围内现有排班。继续？"):return
        end=start+timedelta(days=days)
        self.data["assignments"]=[a for a in self.data["assignments"] if not(start.isoformat()<=a["date"]<end.isoformat())]
        # 已排工时负担；按岗位分组轮换，优先选择较少班次且满足休息间隔的员工
        counts={e["id"]:0 for e in staff}
        last_end={}
        assignments=[]
        for day_i in range(days):
            d=start+timedelta(days=day_i)
            for s in shifts:
                try:
                    st=datetime.combine(d,datetime.strptime(s["start"],"%H:%M").time())
                    en=datetime.combine(d,datetime.strptime(s["end"],"%H:%M").time())
                    if en<=st:en+=timedelta(days=1)
                except:continue
                # 每个班次默认目标人数为最低人数；可在班次设置调整
                target=max(1,int(s["min"]))
                eligible=[]
                for e in staff:
                    prev=last_end.get(e["id"])
                    if prev is not None and (st-prev).total_seconds()/3600 < int(self.data.get("settings",{}).get("rest_hours",11)):
                        continue
                    # 避免同一天安排多班
                    if any(x["employee_id"]==e["id"] and x["date"]==d.isoformat() for x in assignments):continue
                    eligible.append(e)
                eligible.sort(key=lambda e:(counts[e["id"]], random.random()))
                for e in eligible[:min(target,len(eligible))]:
                    assignments.append({"date":d.isoformat(),"shift":s["name"],"time":s["start"]+"-"+s["end"],"employee_id":e["id"]})
                    counts[e["id"]]+=1;last_end[e["id"]]=en
        self.data["assignments"].extend(assignments)
        self.save();self.refresh_all()
        messagebox.showinfo("完成",f"已生成 {len(assignments)} 条排班记录。\n如部分班次人数不足，请增加可排员工或调整休息间隔 / 班次最低人数。")

    def edit_assignment(self):
        sel=self.roster.selection()
        if not sel:messagebox.showinfo("提示","请先选择一条排班记录。");return
        vals=self.roster.item(sel[0],"values")
        old_date,_,old_shift,_,old_emp,_=vals
        idxs=sorted(self.data["assignments"],key=lambda x:(x["date"],x["shift"],x["employee_id"]))
        target=idxs[int(sel[0])]
        win=tk.Toplevel(self.root);win.title("手动调整排班");win.resizable(False,False);win.grab_set()
        frm=ttk.Frame(win,padding=16);frm.pack()
        dvar=tk.StringVar(value=target["date"]);svar=tk.StringVar(value=target["shift"])
        emap={e["name"]:e["id"] for e in self.data["employees"]}
        current=next((e["name"] for e in self.data["employees"] if e["id"]==target["employee_id"]),old_emp)
        evar=tk.StringVar(value=current)
        for i,(lab,var) in enumerate([("日期",dvar),("班次",svar),("员工",evar)]):
            ttk.Label(frm,text=lab).grid(row=i,column=0,sticky="w",pady=5)
            values=[s["name"] for s in self.data["shifts"]] if lab=="班次" else (list(emap) if lab=="员工" else None)
            if values:ttk.Combobox(frm,textvariable=var,values=values,state="readonly",width=22).grid(row=i,column=1,pady=5)
            else:ttk.Entry(frm,textvariable=var,width=25).grid(row=i,column=1,pady=5)
        def save_edit():
            try:date.fromisoformat(dvar.get())
            except:messagebox.showerror("日期错误","日期格式应为 YYYY-MM-DD");return
            shift=next((s for s in self.data["shifts"] if s["name"]==svar.get()),None)
            if not shift or evar.get() not in emap:messagebox.showerror("错误","请选择有效班次和员工");return
            target.update(date=dvar.get(),shift=shift["name"],time=shift["start"]+"-"+shift["end"],employee_id=emap[evar.get()])
            self.save();self.refresh_all();win.destroy()
        ttk.Button(frm,text="保存调整",command=save_edit).grid(row=3,column=0,columnspan=2,pady=10)
    def delete_assignment(self):
        sel=self.roster.selection()
        if not sel:return
        idxs=sorted(self.data["assignments"],key=lambda x:(x["date"],x["shift"],x["employee_id"]))
        target=idxs[int(sel[0])]
        if messagebox.askyesno("确认","删除选中的排班记录？"):
            self.data["assignments"].remove(target);self.save();self.refresh_all()

    def export_csv(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV 文件","*.csv")],initialfile="排班表.csv")
        if not path:return
        emap={e["id"]:e for e in self.data["employees"]}
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f);w.writerow(["日期","班次","时间","员工","岗位"])
            for a in sorted(self.data["assignments"],key=lambda x:(x["date"],x["shift"])):
                e=emap.get(a["employee_id"],{})
                w.writerow([a["date"],a["shift"],a["time"],e.get("name",""),e.get("role","")])
        messagebox.showinfo("导出成功",f"文件已保存：\n{path}")

if __name__ == "__main__":
    root=tk.Tk()
    try: ttk.Style().theme_use("vista")
    except: pass
    RosterApp(root)
    root.mainloop()
