Search.setIndex({docnames:["docs/adr/0001-record-architecture-decisions","docs/adr/0002-use-pytest-bdd-for-bdd-testing","docs/adr/0003-use-django-rest-framework","docs/adr/0004-xml-export-and-import","docs/adr/0005-use-model-tracking-and-workbaskets","docs/adr/0006-use-django-polymorphic","docs/adr/0007-changes-go-through-a-stateful-workflow","docs/adr/0008-simplify-workflow-states","docs/adr/0009-record-generated-envelopes","docs/adr/0010-convert-the-importer-to-a-pipeline","docs/adr/index","docs/code","docs/importer/handlers","docs/importer/index","docs/importer/nursery","docs/importer/parsers_and_namespaces","docs/importer/taric","docs/index","docs/project"],envversion:{"sphinx.domains.c":1,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":1,"sphinx.domains.javascript":1,"sphinx.domains.math":2,"sphinx.domains.python":1,"sphinx.domains.rst":1,"sphinx.domains.std":1,sphinx:56},filenames:["docs/adr/0001-record-architecture-decisions.rst","docs/adr/0002-use-pytest-bdd-for-bdd-testing.rst","docs/adr/0003-use-django-rest-framework.rst","docs/adr/0004-xml-export-and-import.rst","docs/adr/0005-use-model-tracking-and-workbaskets.rst","docs/adr/0006-use-django-polymorphic.rst","docs/adr/0007-changes-go-through-a-stateful-workflow.rst","docs/adr/0008-simplify-workflow-states.rst","docs/adr/0009-record-generated-envelopes.rst","docs/adr/0010-convert-the-importer-to-a-pipeline.rst","docs/adr/index.rst","docs/code.rst","docs/importer/handlers.rst","docs/importer/index.rst","docs/importer/nursery.rst","docs/importer/parsers_and_namespaces.rst","docs/importer/taric.rst","docs/index.rst","docs/project.rst"],objects:{"importer.handlers":{BaseHandler:[12,1,1,""],BaseHandlerMeta:[12,1,1,""],MismatchedSerializerError:[12,3,1,""]},"importer.handlers.BaseHandler":{build:[12,2,1,""],clean:[12,2,1,""],dispatch:[12,2,1,""],get_generic_link:[12,2,1,""],post_save:[12,2,1,""],pre_save:[12,2,1,""],register_dependant:[12,2,1,""],resolve_dependencies:[12,2,1,""],resolve_links:[12,2,1,""],serialize:[12,2,1,""]},"importer.namespaces":{RegexTag:[15,1,1,""],Tag:[15,1,1,""]},"importer.nursery":{HandlerDoesNotExistError:[14,3,1,""],TariffObjectNursery:[14,1,1,""],get_nursery:[14,4,1,""]},"importer.nursery.TariffObjectNursery":{get_handler:[14,2,1,""],register_handler:[14,2,1,""],submit:[14,2,1,""]},"importer.parsers":{ElementParser:[15,1,1,""],IntElement:[15,1,1,""],InvalidDataError:[15,3,1,""],ParserError:[15,3,1,""],TextElement:[15,1,1,""],ValidityMixin:[15,1,1,""],Writable:[15,1,1,""]},"importer.parsers.ElementParser":{clean:[15,2,1,""],data_class:[15,5,1,""],is_parser_for_element:[15,2,1,""],start:[15,2,1,""],validate:[15,2,1,""]},"importer.parsers.IntElement":{clean:[15,2,1,""]},"importer.parsers.TextElement":{clean:[15,2,1,""]},"importer.parsers.Writable":{"delete":[15,2,1,""],create:[15,2,1,""],update:[15,2,1,""]},"importer.taric":{Envelope:[16,1,1,""],EnvelopeError:[16,3,1,""],Message:[16,1,1,""],Record:[16,1,1,""],Transaction:[16,1,1,""]},importer:{handlers:[12,0,0,"-"],namespaces:[15,0,0,"-"],nursery:[14,0,0,"-"],parsers:[15,0,0,"-"],taric:[16,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","method","Python method"],"3":["py","exception","Python exception"],"4":["py","function","Python function"],"5":["py","attribute","Python attribute"]},objtypes:{"0":"py:module","1":"py:class","2":"py:method","3":"py:exception","4":"py:function","5":"py:attribute"},terms:{"1st":3,"50mb":8,"abstract":9,"boolean":4,"case":[5,7,8,12,15,18],"catch":7,"class":[5,9,12,14,15,16],"default":5,"export":[6,10,17,18],"final":[6,7,12],"function":[1,7,8,9,12,14],"import":[10,11,17,18],"int":[8,15,16],"long":9,"na\u00efv":4,"new":[1,4,6,8,9,12,14],"null":[4,5],"return":[5,6,7,8,9,12],"throw":14,"true":[5,7,9,12,16],"try":[8,9,12],"while":9,AND:5,AWS:3,Adding:8,And:18,But:[5,9,12],CDS:[4,6,7,8],FKs:4,For:[0,4,8,9,12],IDs:[3,4,6,8],NOT:4,Not:15,One:5,The:[1,2,3,4,5,6,7,8,11,17,18],Then:1,There:[3,4,5,7,8,9],These:[7,9],Use:[10,17,18],Using:3,Was:6,With:[4,6,9,12],_link:12,_needs_:12,aaa:15,abil:5,abl:[9,14],about:[2,7,8,12],abov:[0,5,6,9,12],accept:[0,1,4,8,12],access:5,accommod:12,accord:8,account:[3,6,8,12],achiev:5,across:[5,6,8],act:[4,9],action:[6,9],actual:[4,6,12,18],adapt:[7,9],add:[3,4,5,9,12],added:[7,8,12,14],adding:[9,12,15],addit:[3,5,7,8,9,15],adopt:[6,7],adr:[0,3,4,5,6,7],advanc:7,advantag:4,affect:[4,5,8],aforement:12,after:[3,8,12,14],again:[6,7],against:[3,5,8,9,12,14],agenc:3,agre:8,alia:15,all:[4,6,8,9,12,14,15,18],allow:[2,4,5,6,9,12,14,15],almost:12,along:[6,8],alreadi:[1,2,3,4,5,6,8,15],also:[3,4,5,6,7,8,9,12,15],altern:[2,10,18],although:5,alwai:[5,6,7,8],amount:[1,2,9],amqp:3,analyst:1,ani:[3,4,5,8,9,12,15,18],anoth:[4,5,7,8,9,12],anyth:9,anywai:6,api:[2,3,6,8,9],app:[1,3,4,9,15],app_label:5,appear:[7,8],appli:[4,5,6,8],applic:[3,4],approach:[4,5,9],appropri:[5,9,12],approv:[3,4,6,7],approval_reject:6,architectur:[17,18],archiv:7,aren:12,argument:12,aris:6,around:[4,8],arriv:9,articl:0,ascend:3,ask:12,assign:[3,9,12],associ:[7,8],assum:[3,6,12],assumpt:[6,9],assur:9,attach:[4,12],attempt:[9,12],attribut:[4,5,8,9,12,15],audit:[4,5,6],authoris:6,autom:8,automat:[1,5,8,9,12],avail:3,avoid:5,await:14,awaiting_approv:6,awaiting_cds_upload_create_new:6,awaiting_cds_upload_delet:6,awaiting_cds_upload_edit:6,awaiting_cds_upload_overwrit:6,awar:5,back:[6,7,8],base:[3,4,5,6,8,9,12,15],basehandl:[12,14],basehandlermeta:12,basi:[5,8],basic:9,basket:3,batch:18,bdd:[10,17,18],becaus:[5,6,7,9],becom:[5,6],been:[3,4,6,7,8,9,12],befor:[4,6,7,8,9,12],begin:8,behaviour:7,being:[3,4,5,6,18],belat:9,below:[5,12],benefit:[5,9],better:[2,3,5,8],between:[1,5,7,9,14],big:9,blank:[5,6],blocker:4,boilerpl:[2,12],bool:[12,15,16],booleanfield:5,border:[3,6],both:[5,6,7,8,9,12],branch:7,build:[2,3,8,9,12,14,15],builtin:15,busi:[1,3,8,9],bypass:3,cach:[8,12,14],call:8,callabl:8,can:[1,3,4,5,6,7,8,9,12,14,15],cannot:[6,9,12],care:9,carri:[7,9],cascad:12,caus:7,cds_error:6,centralis:3,certain:[5,6,9],chanc:4,chang:[3,4,7,8,9,10,15,17,18],changeabl:5,charfield:[4,5],check:[5,12,15,18],checksum:8,child:[15,18],childel:15,children:[5,15],choic:[3,4],choos:8,chosen:1,classmethod:[12,14],claus:5,clean:[4,5,12,15,18],client:[8,9],clone:[6,7],close:9,closest:2,cluster:9,code:[2,3,4,8,12,15,17,18],codebas:8,cohes:3,collabor:1,collect:[5,9,12],column:[4,6,9,18],come:[5,8,9,12,14],command:3,commod:5,common:[5,12],commun:8,compar:9,compil:12,complet:[7,9,12],complex:[4,5,7,8,18],compon:[5,8,9],con:[5,18],concept:[6,7,8],conceptu:9,concern:4,conclus:5,concret:[4,5],condit:8,conflict:4,connect:[4,5],consequ:[10,18],consequenti:[9,12],consid:[4,10,18],consist:4,constrain:5,constraint:6,consum:[2,8],contain:[6,8,9,12,15],content:[4,5,9,17],content_typ:5,context:[10,18],contigu:3,continu:[1,7],contribut:18,control:[3,6,8,9],conveni:[5,14,15],convert:[3,10,14,17,18],copi:[3,5],core:9,correct:[8,9],correspond:[8,15],cost:5,could:[5,8,9,12],coupl:[3,9],cours:9,cover:18,coverag:1,creat:[4,5,6,7,8,9,12,15],creator:4,criteria:1,cron:3,cue:9,current:[3,4,6,8,9,12],custom:[4,9,12],customis:[12,18],dai:[3,8],daili:3,data:[1,2,3,4,6,7,8,12,14,15,18],data_class:15,databas:[3,5,6,8,9,12,14,15],dataset:12,date:[0,1,2,3,4,5,6,7,8,9,15],deal:[5,8],debug:6,decid:7,decis:[17,18],decor:12,decoupl:18,deem:12,def:[8,12],defin:[7,8,9,12,15],definit:[6,9],delet:[4,6,15],demand:12,denot:12,depdend:9,depend:[5,6,8,12,14,18],dependentmodelahandl:12,dependentmodelapars:12,dependentmodelbhandl:12,dependentmodelbpars:12,dependentmodelseri:12,deploy:18,depth:[15,16],describ:[0,5,7,9],descript:[4,6,7,8,18],design:[5,7,8,9,12,14],desir:[5,9,12],detail:5,detect:6,determin:9,dev:2,develop:[1,3,5,9],diagram:9,dict:[9,12,15],dictionari:[9,12,14],dies:9,diff:5,differ:[5,6,8,12],differenti:[3,12],difficult:[5,8],difficulti:12,digit:3,digraph:7,direct:7,directli:[3,5],discontinu:6,discov:8,discuss:5,dispatch:[9,12,14],dispatched_object:12,dispatchedobjecttyp:[12,14],displai:3,dit200001:8,dit:8,django:[10,14,17,18],doc:[13,17],document:[1,2,3,6],doe:[6,8,9,18],doesn:[12,18],doing:5,domain:6,don:[6,8,9,15,18],done:[4,5,6,9],down:7,download:[3,6],draft:[4,5,6],drf:2,due:[1,5,12],duplic:3,dure:4,each:[3,4,5,8,9,12],earlier:6,eas:[7,9],easi:[1,4,5],easier:[1,5,9],easili:[2,5,12],edit:[4,6,7,12],effect:[6,9,12],effici:5,effort:3,either:[5,6,8,9],element:[8,9,15],elementpars:[9,15],elementtre:15,elemnt:9,emit:9,empti:[8,12],enabl:[3,9],end:[6,7,8,9,15],engin:3,enough:[6,8,12,15],ensur:[8,12],enter:12,entir:[8,9],entiti:15,entrypoint:14,envelop:[3,6,7,9,15,16],envelope_count:8,envelopeerror:16,equival:1,erron:8,error:[3,4,6,7,8,9,12,14],especi:3,essenc:5,essenti:[5,8],etc:[2,3],etre:[3,15],even:[7,8,9,12],event:4,ever:5,everi:[3,5,8,12],everyth:[5,9],exact:7,exampl:[8,12,15,18],except:[12,14,15,16],execut:[3,5],exemplifi:5,exist:[1,4,6,8,12,18],expect:[8,9,12],experi:[7,9],explanatori:4,explicit:12,explicitli:5,expos:6,extens:9,extern:[6,8],extra:[5,9,12],extract:[9,12,18],fact:14,factor:9,fail:[6,9,12],failur:[3,8,12],fallback:12,fals:[5,6,9,12,15,16],falsi:9,familar:1,familiar:2,far:9,fashion:8,fast:6,featur:1,fetch:[5,9,12],few:[4,12,15],field2:12,field:[4,12,15],file:[4,9],filenam:8,filter:6,find:[5,9,14],finish:9,finit:[4,6],first:[3,5,8,9,12],firstli:12,fit:18,flag:6,flexibl:[8,12],flip:4,flow:9,focu:12,follow:[5,7,8,9,12,15],footnot:[5,8],footnote_type_id:5,footnotetyp:5,forc:5,foreign:[5,12,18],foreignkei:5,foremost:5,form:[1,3,5,7,8],format:[1,8,9],forward:12,found:[5,6,9,12,14],four:4,fragil:9,framework:[1,10,17,18],from:[3,4,6,7,8,9,12,14,18],full:[3,7,9],further:[4,5,8,9,12],futur:[6,8,10,18],gatewai:[8,9],geneat:8,gener:[1,3,4,5,9,12,14],generate_envelop:8,generate_tar:5,genericforeignkei:4,get:[4,6,8,9,12,18],get_:12,get_generic_link:12,get_handl:14,get_latest_vers:12,get_link_to_model_b_link:12,get_nurseri:14,gherkin:1,give:5,given:[1,4,5,6,7,9,12,14,15],goe:12,going:6,good:[6,9],goodsnomenclatur:[7,9],goodsnomenclatureorigin:9,goodsnomenclaturesuccessor:9,graph:7,group:[3,5,7,8],guarante:[9,12],guernsei:3,had:[8,9],half:5,halt:9,hand:5,handl:[3,4,5,7,8,12,14,15,18],handler:[11,13,14,17,18],handlerdoesnotexisterror:14,happen:[8,9],happi:7,hard:6,harder:9,has:[4,5,6,7,8,9,12],hasn:4,have:[1,3,4,5,6,7,8,9,12,15],heavili:9,henc:8,here:[9,12],hierarch:7,high:5,highli:18,histor:[5,9],histori:6,hit:5,hmrc:[3,4,6],hold:[4,5,9,12],how:[4,5,6,9,12],howev:[3,4,5,8,9,12],http:3,idea:4,identifi:[3,4,9,12],identifying_field:12,ignor:9,ill:7,immedi:[9,12],immut:[4,6],impact:[7,9],implement:[2,4,5,6,15,18],implic:2,imposs:9,includ:[5,7,8,11,12,18],incom:[12,14],incomplet:[14,18],incorpor:3,increas:[3,4,6],increasingli:5,incred:5,increment:3,indetermin:9,index:[5,6,17],indic:9,individu:[4,5,8,9],ineffici:5,inform:8,ingest:18,inher:4,inherit:[4,10,17,18],init:12,initi:[5,9,12],initialis:12,inner:5,input:9,insert:[9,12],instal:18,instanc:[5,12],instead:[3,5,6,9],instruct:6,integ:[4,15],integr:[4,9],intel:15,intend:12,interact:[5,7,8,9],interdepend:[4,9],interfac:[6,9,14,15],intermedi:[3,4,5,9],intern:[6,8,14],internet:3,interpret:1,interv:3,intric:18,introduc:[4,6,7,9],introspect:15,invalid:7,invaliddataerror:15,involv:[4,9],ireland:3,is_parser_for_el:15,issu:[9,12],item:[4,6,9],iter:[5,12],its:[4,6,9,15],itself:[4,5,6,9,12],januari:3,jersei:3,jinja2:3,job:3,join:[5,6],journei:6,json:[3,15],just:[3,6,9,12],karg:12,keep:[4,5,6,8,9,15],kei:[4,5,7,12,18],know:[6,9,15],known:8,kwarg:[12,16],lack:[4,5,9],larg:[1,2,3,5,8],larger:8,last:[3,4],lastli:9,latenc:3,later:[9,12,14],latest:6,latter:12,layer:14,lean:5,learn:[1,7],learnt:8,leav:9,legaci:9,let:[4,9],level:[9,12,18],librari:[3,4,5],light:4,lightweight:0,like:[4,5,8,9,12],likewis:5,limit:[4,5,8],line:3,link:[0,4,5,12,18],link_nam:12,link_to_model_a:12,link_to_model_b:12,linkedobjecthandl:12,linkstyp:12,linktomodela:12,linktomodelb:12,list:[5,8,12],littl:[8,9],live:[4,5,6],local:9,logic:[5,8],longer:6,look:[5,6,9,14],lookup:15,loop:12,lot:9,lower:4,lxml:3,machin:[4,6],made:[0,3,4,5,6,9],mai:[3,4,6,7,8,9,12,15],main:[4,9],maintain:[3,4],major:[4,7],make:[4,5,6,8,9,18],manag:[3,4,5,6,7,8,9],mani:[7,8,12,15,16,18],manual:[7,8],map:[8,14,15],mask:5,massiv:4,match:[8,9,12,14,15],matter:9,max_length:5,maximum:8,me32:8,mean:[6,8,9,12,18],measur:[3,8],mechan:[5,6,9,12],medium:9,memori:[3,9],merg:[4,7,9,12],messag:[3,8,9,15,16],metaclass:12,metadata:8,method:[3,4,5,12,14],michael:0,might:8,migrat:9,mileston:9,mind:[4,9],minim:8,minimum:[4,5,6,8],mismatchedserializererror:12,miss:14,mixin:5,mock:4,mode:8,model:[3,6,7,8,9,10,12,14,17,18],modelseri:12,modif:3,modul:[3,7,17],more:[2,3,5,6,7,8,12,18],most:[4,5,6,7,8,9,12],mostli:9,motiv:7,move:[7,9],msg:15,mti:18,much:[2,7],multi:[10,17,18],multipl:[4,5,8],must:[3,4,5,6,7,8,12],naiv:9,name:[4,9,12,15],namespac:[9,11,13,16,17],nat:0,nativ:5,natur:[5,12],necessari:[4,5,7,8,12],necessarili:[3,8,12],need:[0,3,4,5,6,7,8,9,12,14,15],neglig:5,nest:15,never:[5,6],new_in_progress:6,newli:[6,9],next:[5,6],nnn:3,non:[9,12],none:[12,14,15,16],nor:[9,12],normal:5,northern:3,note:[7,9],noth:12,notif:3,notion:8,now:7,nullabl:[5,6,12],number:[3,4,5,7,8,9],numer:[3,5,8],nurseri:[11,12,13,15,17,18],nygard:0,obfusc:5,obj:[12,14],object:[3,4,6,12,14,15,18],objectcachefacad:14,obvious:5,occas:[5,12],occur:8,often:14,old:[1,8],on_delet:5,onc:[4,5,6,7,9,12],one:[4,8,9,12,14,18],onetoonefield:5,onli:[4,5,6,7,8,15],onto:9,oper:[5,6,8],operation:6,opportun:12,oppos:4,option:[5,12,15,16,18],order:[3,6,8,9],ordin:12,orient:5,origin:[7,9],orm:[4,5],other:[4,5,6,8,9,12,18],other_model:12,oub:15,our:[1,2,8],out:[6,7,8],output:[3,7,8,15],over:[3,8,9,12],overlap:5,overrid:5,overridden:12,overwritten:9,own:3,pack:8,page:17,parent:[5,9,15],parentel:15,pars:[3,9,15],parser:[11,12,13,17,18],parsererror:15,part:[3,4,7,9,12],partial:[3,6,8,9],particular:8,particularli:[8,15],partli:8,pass:[8,9],past:[7,8],path:[7,8],pattern:[4,5,8,15],pend:[6,7],per:[3,6,8],perform:[5,6],period:8,person:4,piec:[9,14],pipelin:[10,17,18],place:[6,8,12],point:[5,12],polymorph:[4,10,17,18],polymorphic_ctyp:5,polymorphic_ctype_id:5,polymorphicmodel:5,polymorphicqueryset:5,popular:2,posit:[4,6],possibl:[4,5,6,8],post:12,post_sav:12,power:[6,7],pre:[1,8,12],pre_sav:12,preclud:9,predecessor:[4,5,6],prefix:[9,12,15],prep:15,prepend:8,present:[7,9],previou:[4,5,6,7,8],previous:[9,12],primari:[4,5,14],primarili:4,print:5,pro:[5,18],probabl:9,problem:[5,18],process:[3,4,6,7,8,12,14,15,18],produc:3,product:7,progress:5,project:[0,1,2,5,9,17],properli:12,propos:[2,4,5,7,8,9],protect:5,prove:1,provid:[3,8,12,14,15],pryce:0,publish:[1,3,6,7],purpos:[4,5,6,7,8,9],put:[8,9],pytest:[10,17,18],python:[9,14],queri:[4,6,12,18],queryset:5,quickli:8,quit:[4,5],rais:[9,12],rang:9,rapidli:5,rare:5,rather:[5,8],raw:14,reach:9,read:3,readi:[9,12],ready_for_export:6,realis:[6,9],reason:[5,6,7,10,18],rebuild:12,receipt:[6,7],receiv:[3,7,9,12,14],recent:8,record:[3,5,6,8,12,15,16,17,18],recurs:9,redevelop:9,redi:9,reduc:[3,7,12],redund:7,refer:[3,12],referenc:12,reflect:[4,9],regard:3,regextag:15,regist:[12,14],register_child:15,register_depend:12,register_handl:14,registr:12,reject:[4,6,7,8],rel:[5,9,12],relat:[4,5,9,12],related_nam:5,relationship:8,relev:[4,5,9,12],reli:[12,18],rememb:6,remov:[5,6,7,12],render:3,replac:[1,6,8,9],report:[1,3],repres:[4,5,6,7,8],represent:2,reprocess:9,reqir:8,request:[2,6],requir:[1,3,4,5,6,7,8,9,12],reset:8,resolv:[9,12],resolve_depend:12,resolve_link:12,resolved_link:12,resourc:[2,3],respons:[6,7,8,9],rest:[10,14,17,18],resubmiss:6,result:[1,4,5,9,14],retain:6,retir:8,retrospect:12,reus:[8,9],revers:5,review:[4,8],risk:4,root:8,roughli:9,rout:2,routin:7,row:[4,5,6,9,14],rule:[3,8,9],run:[3,4,5,6,12],sadli:12,safe:6,said:5,same:[3,5,7,8,9,12,15],save:[2,3,12,16],scenario:[1,12],schedul:[3,6,7],schema:[3,8],script:3,search:[12,17],second:[5,8,12],section:18,see:[0,1,5,6],select:[5,6,15],self:[4,5,12,15],send:[3,6,7,8],sens:8,sent:[4,6,7,8],sent_to_cd:6,sent_to_cds_delet:6,separ:[3,5,6,8,9,14],sequenc:[3,8],sequenti:[4,6,7,8,9],seri:4,serial:[12,18],serializ:12,serializer_class:12,seriou:9,serv:[4,7],set:[5,6,8,9,12],sever:[3,8,9,12],sftp:3,share:[1,5,12],should:[4,5,6,7,8,9,12,15,18],show:5,shown:[6,7],sid:[6,15],signatur:8,signifi:12,signific:[4,5,9],similar:[3,9],similarli:9,simpl:[4,5,9,12,15],simpleobjecthandl:12,simpleobjectpars:12,simpleobjectseri:12,simpler:7,simpli:[9,12],simplifi:[2,5,9,10,17,18],sinc:[5,8],singl:[5,6,7,8,9],singular:9,size:8,slow:7,softwar:6,solut:[5,18],solv:[5,12],solvabl:5,some:[3,4,5,6,7,8,9,12,14],some_field:[12,15],some_other_model_id:12,someothermodel:12,someth:[6,9],sometim:[5,6],somewher:1,sort:[8,18],spec:8,special:[3,8],specif:[1,5,8,11,12,15],specifi:4,split:[4,8,9],sql:18,stage:[6,8,12],stai:[4,8],stakehold:1,stand:7,standard:[4,9],standpoint:5,start:[3,5,6,7,8,9,15],state:[4,5,10,17,18],statement:5,statu:[10,18],step:[4,7,9,12],still:[3,4,6,7,8,18],stop:[4,9,12],storag:9,store:[3,5,8,9,12,14],stori:1,str:14,straggl:9,straight:[5,7],strict:[9,12],string:12,structur:[9,15],stuck:9,style:[4,6,12],subject:4,submiss:4,submit:[4,6,7,8,14,15],submitt:6,subrecord:8,subsequ:[3,8],substanti:8,succeed:9,success:[9,12],successor:5,suggest:[10,18],suitabl:6,summari:5,supersed:[3,6],support:[2,5,7,8],suppos:12,surprisingli:5,system:[3,4,5,6,7,8,9,12,14],tabl:[4,6,8,9,10,15,18],tag:[9,12,14,15,16],take:[5,6,8,9,12,14],taken:[6,9],tamato:[1,3,4,5,8,9],tamato_usernam:16,tap:1,taric3:[3,4,5,8,9,15],taric:[3,6,8,9,11,13,17],taric_compon:5,tariff:[3,4,5,6,7,8,9,14],tariffobjectnurseri:[12,14],tastypi:2,team:[1,2,3],templat:[3,5],term:[4,5,6,9],ters:9,test:[10,17,18],text:15,textel:[9,15],than:[2,5,8,12],thei:[4,6,7,8,9,12,14],them:[1,5,6,8,9,12],themselv:[3,14],therefor:[4,5,7,8,9,12],thi:[0,3,4,6,7,8,9,11,12,14,15,18],thing:[6,8],think:[2,6],those:[4,5,7,12],three:[8,9],through:[4,5,8,9,10,12,17,18],thu:[5,6],tied:9,tightli:9,time:[3,4,5,6,12],todo:8,togeth:[5,9,12],too:8,tool:[0,1,3,4,5,6,9],toolset:0,total:5,track:[5,6,8,10,15,17,18],tracked_model:5,tracked_object:5,trackedmodel:[6,12,18],trackedmodel_ptr_id:5,trade:[7,8],transact:[3,4,6,7,9,16],transaction_count:8,transaction_id:[6,9],transactionid:4,transfer:[3,8],transit:4,treat:9,tree:7,tri:9,trial:4,trivial:9,ttm:[7,8],turn:9,two:[3,4,5,6,7,8,9,12],type:[4,9,12,14,15,18],undefin:8,underli:4,underpin:4,understand:[1,7,8,9],unhappi:[7,8],unifi:12,uniqu:[3,4,5,18],unknown:8,unless:[3,5],unlik:[5,7],unnecessari:9,unsuccess:3,until:[8,9,12,14],updat:[3,4,6,8,15],update_typ:6,upload:[3,4,7],use:[0,1,5,6,7,8,9,12],used:[5,7,8,9,12,14],useful:5,user:[1,2,3,4,6,7,9],uses:[5,9,15],using:[1,3,4,8,9],usual:3,util:[12,14],valid:[3,4,5,6,7,8,9,12,15],valid_footnote_type_id:5,validitymixin:[5,15],valu:[8,9,15],vari:[6,9],varieti:7,variou:[6,7],vat:3,veri:[4,5,9,12],version:[2,4,6,8],via:[3,14],view:[1,4,7,8],vpc:3,wai:[3,4,5,8,9,12,15],wait:[6,7,9,12],want:[1,2,9,15],weaker:5,weigh:5,well:[7,12,18],were:[4,5,6,8,9],what:[6,8,12,18],whatev:12,when:[1,4,5,6,8,9,12,14,15],where:[3,4,5,6,7,8,9,12,15],whether:[4,12,14,15],which:[3,4,5,6,7,8,9,12,14,15,18],whilst:[9,12],who:[4,9],wholli:8,within:[3,4,5,8,12,15,18],without:[5,6,8,12],work:[3,5,7,12,18],workabl:12,workbasket:[3,6,7,8,9,10,17,18],workbasket_id:[5,15],workbasket_statu:16,workflow:[10,17,18],workflowst:7,worth:[7,9],would:[3,4,5,7,8,9,12],wrap:9,writabl:15,write:[1,2,3,15],written:[1,9],xml:[4,6,8,10,15,17,18],xsd:8,xxxx:8,year:[3,8],yet:[4,6,7,9,12,15],you:5,yynnn:3,yyxxxx:8},titles:["1. Record architecture decisions","2. Use pytest-bdd for BDD testing","3. Use Django REST Framework","4. XML Import and Export","5. Use tracked models and workbaskets","6. Use Django Polymorphic for Multi-Table Inheritance","7. Changes go through a stateful workflow","8. Simplify workflow states","9. Generate envelope files","10. Convert the XML importer to a pipeline","Architectural Decision Records","Code Documentation","The Importer - Handlers","The Importer","The Importer - The Nursery","The Importer - Parsers and Namespaces","The Importer - Taric","Welcome to TaMaTo\u2019s documentation!","Project Documentation"],titleterms:{"case":9,"export":3,"import":[3,9,12,13,14,15,16],The:[9,12,13,14,15,16],Use:[1,2,4,5],actual:[5,9],all:5,altern:[5,9],architectur:[0,10],batch:9,bdd:1,being:9,cach:9,chang:[5,6],check:9,child:5,childmodel:5,clean:9,code:[5,9,11],column:5,complex:9,con:9,consequ:[0,1,2,3,4,5,6,7,8,9],consid:9,content:18,context:[0,1,2,3,4,5,6,7,8,9],convert:9,customis:9,data:[5,9],decis:[0,1,2,3,4,5,6,7,8,9,10],decoupl:9,depend:9,descript:5,django:[2,5],document:[11,17,18],doe:5,doesn:9,envelop:8,exampl:[5,9],exist:9,extract:3,file:8,foreign:9,framework:2,from:5,futur:9,gener:8,get:5,handl:9,handler:[9,12],highli:9,hmrc:8,http:8,implement:9,incomplet:9,indic:17,ingest:3,inherit:5,interfac:8,intric:9,kei:9,link:9,mani:9,mean:5,model:[4,5],more:9,mti:5,multi:5,namespac:15,nurseri:[9,14],object:[5,9],one:5,option:9,parser:[9,15],pipelin:9,polymorph:5,pro:9,problem:9,process:9,project:18,pytest:1,queri:5,reason:4,record:[0,9,10],reli:9,rest:2,serial:9,simplifi:7,solut:9,sort:9,sql:5,state:[6,7],statu:[0,1,2,3,4,5,6,7,8,9],still:9,suggest:9,tabl:[5,17],tamato:17,taric:16,test:1,thi:5,through:6,track:4,trackedmodel:[4,5],transact:8,type:5,uniqu:9,welcom:17,well:9,what:5,within:9,work:9,workbasket:[4,5],workflow:[6,7],xml:[3,9]}})