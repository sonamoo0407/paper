import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url)).replaceAll('\\', '/').replace(/\/$/, '');
const build = fileURLToPath(new URL('.', import.meta.url)).replaceAll('\\', '/').replace(/\/$/, '');
const blue = '#2459AA';
const ink = '#20262E';
const gray = '#586474';
const font = 'Malgun Gothic';
let nativeImages = false;
const source = {
  netminer: 'https://www.netminer.com/kr/netminer/methodology.php',
  citracer: 'https://github.com/marcpinet/citracer',
  networkx: 'https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.centrality.betweenness_centrality.html',
  logo: 'https://www.kyonggi.ac.kr/www/contents.do?key=5093',
  logoAsset: 'https://www.kyonggi.ac.kr/site/www/images/contents/key5093_img01_.svg',
  project: 'https://github.com/sonamoo0407/paper',
  openai: 'https://openai.com/codex/',
};

function text(slide, value, x, y, w, h, size = 26, bold = false, color = ink) {
  const shape = slide.shapes.add({geometry: 'textbox', position: {left:x, top:y, width:w, height:h}, fill:'none', line:{fill:'none', width:0}});
  shape.text = value;
  shape.text.style = {typeface:font, fontSize:size, bold, color, autoFit:'none'};
  return shape;
}

function rect(slide,x,y,w,h,fill) {
  return slide.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});
}

async function logo(slide, x=44, y=650, w=64, h=44) {
  const filePath=`${build}/assets/kgu-official.png`;
  const bytes=nativeImages?await fs.readFile(filePath):null;
  const imageSource=nativeImages?{blob:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),contentType:'image/png'}:{path:filePath};
  slide.images.add({...imageSource,alt:'경기대학교 공식 KGU 로고',position:{left:x,top:y,width:w,height:h},fit:'contain'});
}

async function page(presentation, title, notes, citations=[]) {
  const s = presentation.slides.add();
  s.size = {width:1280,height:720};
  s.background.fill = '#FFFFFF';
  rect(s,0,0,1280,88,blue);
  text(s,title,48,20,1180,56,35,true,'#FFFFFF');
  await logo(s);
  text(s,String(presentation.slides.items.length),1190,664,44,25,16,false,gray);
  s.speakerNotes.text = notes + '\n\n자료 기준 2026-11-18\n' + citations.join('\n') + '\nKGU 로고 원본\n' + source.logoAsset;
  return s;
}

function table(s, values, x,y,w,h,widths, size=23) {
  const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
  t.borders.assign({fill:'#D7DFEA',width:1,style:'solid'});
  for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
    const cell=t.getCell(r,c);
    cell.fill=r===0?blue:(r%2?'#FFFFFF':'#F0F4F9');
    cell.text.style={typeface:font,fontSize:size,bold:r===0,color:r===0?'#FFFFFF':ink};
  }
  return t;
}

function sourceLine(s,value,y=612) {text(s,value,132,y,1094,30,15,false,gray);}

async function image(s,path,x,y,w,h,alt,crop) {
  const bytes=nativeImages?await fs.readFile(path):null;
  const imageSource=nativeImages?{blob:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),contentType:'image/png'}:{path};
  s.images.add({...imageSource,position:{left:x,top:y,width:w,height:h},alt,fit:'contain',...(crop?{crop}:{})});
}

export async function buildReport(presentation, options={}) {
  nativeImages=Boolean(options.nativeImages);
  const result=JSON.parse(await fs.readFile(`${build}/results.json`,'utf8'));
  {
    const s=presentation.slides.add();s.size={width:1280,height:720};s.background.fill='#FFFFFF';
    rect(s,0,0,94,720,blue);rect(s,94,626,1186,94,blue);
    await logo(s,1050,42,160,110);
    text(s,'논문 인용망 분석',170,214,1030,76,52,true);
    text(s,'매개중심성과 인용 문맥 점수',172,311,1035,72,38,true,blue);
    rect(s,174,408,980,2,'#263441');
    text(s,'NetMiner 스터디와 citracer 적용 결과',174,444,980,48,27);
    text(s,'정승빈   경기대학교',174,514,900,40,24,false,gray);
    text(s,'2026.11.18 연구 진행 보고',174,651,990,38,23,false,'#FFFFFF');
    s.speakerNotes.text='교수님께 현재 개발된 논문 인용망 분석 기능과 실제 실행 결과를 보고하는 발표다. NetMiner 실습에서 중심성 해석을 공부했고, 실제 프로젝트는 citracer 오픈소스에 인용 문맥 근거 패널과 합의한 채점 규칙을 연결했다. OpenAI Codex는 구현과 자료 작성 지원에 활용했다. 최신 실행 수치와 이전 실행 화면의 기준 시점을 구분한다.\n'+Object.values(source).join('\n');
  }
  {
    const s=await page(presentation,'NetMiner 스터디에서 확인한 분석 방식','NetMiner에 기존 랜섬웨어 논문 10개와 인용 관계 14개를 입력하고 Network > Centrality > Betweenness 분석 보고서를 확인했다. 사용자가 제공한 실행 화면에는 방향성 네트워크와 매개중심성 최댓값 약 0.032가 표시되어 있다. 이 실습은 연결 구조를 수치로 읽는 방법을 이해하기 위한 작업이다. 제품의 PDF 원문 분석 기능이나 모든 기본 계산 옵션까지 실증한 것으로 확대하지 않는다.',[source.netminer,`${root}/outputs/netminer-study-roadmap.md`]);
    text(s,'랜섬웨어 인용망으로 매개중심성 실습',52,128,1170,50,32,true,blue);
    table(s,[['실습 입력','확인한 결과'],['논문 10개와 인용 관계 14개','방향성 네트워크와 중심성 보고서'],['Betweenness Centrality 메뉴','관계 사이를 잇는 중간 논문 후보'],['계산 결과를 시각화에 연결','중심성이 큰 논문을 큰 노드로 표현'] ],52,206,1176,304,[420,756],25);
    text(s,'프로젝트 적용',52,546,255,44,28,true,blue);
    text(s,'인용 관계를 구성하고, 매개중심성과 본문 근거를 함께 확인',310,546,900,70,27);
    sourceLine(s,'참고  NetMiner 공식 Methodology와 기존 랜섬웨어 실습 기록');
  }
  {
    const s=await page(presentation,'매개중심성 계산 방식','노드 v를 중간에 지나는 모든 시작점·도착점 쌍의 최단 경로 비율을 합산한다. 동일 길이의 최단 경로가 여러 개라면 기여를 나눈다. 현재 로컬 citracer analytics.py는 nx.DiGraph에서 nx.betweenness_centrality(G)를 호출한다. 기본 조건은 방향 그래프, 간선 거리 동일, 양 끝점 제외, 정규화다. n=421일 때 정규화 분모는420×419=175980이다. 문맥 점수는 이 거리 입력으로 사용하지 않는다.',[source.networkx,`${root}/external/citracer/citracer/analytics.py`]);
    text(s,'다른 논문 사이의 최단 인용 경로를 잇는 정도',52,128,1170,54,31,true,blue);
    text(s,'BC(v) = Σ [ v를 지나는 최단 경로 수 / 전체 최단 경로 수 ]',52,217,1170,70,29,true);
    table(s,[['간단한 인용 경로','중간 논문 B의 기여'],['A → B → C만 존재','A에서 C로 가는 경로의 기여 1'],['A → C 직접 인용도 존재','더 짧은 직접 경로가 있어 이 쌍의 기여 0'],['같은 길이의 최단 경로가 여러 개','그중 B를 지나는 비율만 반영']],52,320,1176,235,[700,476],23);
    text(s,'방향 그래프 정규화   (n−1)(n−2)로 나눔',52,580,1170,40,25,false,gray);
    sourceLine(s,'계산 근거  NetworkX 공식 문서와 프로젝트의 citracer analytics.py',628);
  }
  {
    const s=await page(presentation,'연구 실행 구조와 사용 도구','Windows에서 기관 접근이 가능한 브라우저로 받은 PDF를 읽기 전용 VMware 공유 폴더로 인계했다. Ubuntu Hermes는 입력 무결성을 검증하고 분석 실행을 연결한다. 전문 참고문헌 및 문맥 추출, 중심성 계산은 Python과 citracer가 담당한다. 최종 HTML은 공유 폴더로 전달하고 파일 해시를 대조했다.',[source.citracer,source.project,`${root}/reports/phishing_windows_handoff_20261118/README.md`]);
    table(s,[['단계','담당','남기는 결과'],['후보 수집과 PDF 확보','경기대 도서관 EDS, Windows Chrome','서지 장부와 검증된 PDF'],['인계와 분석 실행','VMware 공유 폴더, Ubuntu Hermes','파일 해시와 단계별 상태'],['참고문헌 및 문맥 추출','Python 분석 스크립트','R1·R2·R3 인용 근거'],['매개중심성과 그래프','citracer, NetworkX','노드 크기와 인터랙티브 HTML'],['결과 확인과 공유','Hermes와 검토자','검수한 HTML과 일치한 해시']],52,139,1176,430,[270,435,471],23);
    text(s,'R1은 출발 논문, R2는 직접 참고문헌, R3는 한 단계 더 추적한 논문',52,590,1176,55,24,false,gray);
  }
  {
    const s=await page(presentation,'합의한 인용 문맥 가감점','사용자와 합의한 프로젝트 운영 규칙이다. 외부 검증을 마친 표준 중요도 공식이라고 주장하지 않는다. 방법을 실제 채택하거나 발전시켰다는 근거가 있으면 +1.5, 배경 소개와 비교·검증은 +0.5, 구체적인 한계 지적은 -0.5, 인용 관계는 확인했으나 목적이 불분명하면 +0.2다. 한계는 피인용 논문 또는 방법을 특정한 문맥이어야 하며 일반적인 위협 설명을 자동으로 감점하지 않는다.',[`${root}/skills/root-paper-research/CITATION_CONTEXT_RULES.md`]);
    table(s,[['분류','점수','판정 근거'],['방법 채택·발전','+1.5','방법이나 개념을 실제 사용하거나 확장'],['배경·단순 소개','+0.5','관련 연구 또는 배경으로 소개'],['비교·검증','+0.5','실험 비교 대상이나 검증 기준으로 사용'],['한계 지적','−0.5','대상 논문·방법의 구체적인 한계를 명시'],['판정 보류','+0.2','인용은 확인했으나 본문 또는 목적이 불명확']],52,131,1176,402,[290,140,746],24);
    text(s,'같은 방향의 논문 쌍에 한 번 적용하고, 채택 근거가 있으면 우선 반영',52,565,1176,63,25,true,blue);
    sourceLine(s,'점수의 근거  프로젝트에서 합의한 인용 문맥 채점 규칙');
  }
  {
    const s=await page(presentation,'구조 점수와 문맥 근거의 사용','매개중심성은 그래프 구조를 설명하고, 문맥 점수는 개별 인용의 용도를 표시한다. 두 점수를 더하는 공식과 통합 순위는 합의하지 않았다. 원문의 참고문헌 번호, 인용 문장, 주변 문맥, PDF 페이지와 판단 이유를 연결해 검토 가능하게 한다. 중간 논문의 내용상 역할은 들어오는 인용과 나가는 인용을 함께 읽고 해석해야 한다.',[`${root}/skills/root-paper-research/CITATION_GRAPH_RULES.md`,`${root}/skills/root-paper-research/CITATION_CONTEXT_RULES.md`]);
    table(s,[['보는 항목','화면에 반영하는 방식','확인할 내용'],['매개중심성','노드 크기와 후보 순위','어느 인용 경로 사이에 놓이는가'],['문맥 점수','선택한 간선의 점수','소개·채택·비교·한계 중 무엇인가'],['원문 근거','그래프 아래 상세 패널','인용 문장, 주변 문맥, 페이지'],['중간 논문 해석','들어오는 인용과 나가는 인용 대조','어떤 방법·개념을 이어 주는가']],52,160,1176,350,[250,420,506],24);
    text(s,'현재 화면은 매개중심성과 문맥 점수를 각각 표시',52,553,1176,48,30,true,blue);
    sourceLine(s,'통합 가중치와 합산 순위는 후속 검토 항목');
  }
  {
    const s=await page(presentation,'실제 깊이순 인용 그래프 화면','저장된 실제 citracer 브라우저 캡처다. 이 화면은 이전 검수 실행의450노드433인용 결과다. 2026-11-18최종 실행은421노드419간선으로 별도 슬라이드에 보고한다. 파란색 R1, 초록색 R2, 갈색 R3가 보이고 노드 크기 옵션에 매개중심성을 적용했다. 그림 자체의 숫자를 최신 값으로 바꾸지 않았다.',[`${build}/assets/phishing-citracer-depth-review.png`,source.citracer]);
    await image(s,`${build}/assets/phishing-citracer-depth-review.png`,46,111,1188,473,'실제 피싱 인용망 깊이순 검수 화면',{left:0,top:0,right:0,bottom:0.25});
    text(s,'R1 · 출발 논문        R2 · 직접 인용        R3 · 추가 인용',52,599,1176,36,24,true,blue);
    sourceLine(s,'이전 검수 화면  450노드·433인용   /   최신 실행 수치는 다음 결과 표에 제시',657);
  }
  {
    const s=await page(presentation,'실제 간선 선택과 인용 근거 화면','이전 실제 실행 화면에서 인용 간선을 선택한 뒤 아래에 근거 패널이 열린 상태다. 화면에는 배경·단순 소개 +0.5와 참고문헌9번, 참고문헌 PDF6페이지 및 본문 PDF2페이지가 표시된다. 인용문은 URL의 어휘적 내용·특수문자 빈도·의심스러운 단어·URL 패턴을 기존 연구의 특징으로 소개한다. 이 캡처의 데이터는 최신 분석 실행과 구분한다.',[`${build}/assets/phishing-graph-after.png`]);
    text(s,'선택한 인용선의 용도와 원문 근거를 확인',52,127,1176,45,30,true,blue);
    await image(s,`${build}/assets/phishing-graph-after.png`,48,192,1184,245,'실제 하단 인용 문맥 패널을 확대해 표시',{left:0.012,top:0.744,right:0.018,bottom:0.026});
    table(s,[['화면에서 확인한 항목','표시 내용'],['인용 용도와 점수','배경·단순 소개 +0.5'],['원문 근거 위치','참고문헌 [9] / 참고문헌 PDF p.6 / 본문 PDF p.2']],52,476,1176,134,[420,756],23);
    sourceLine(s,'이전 실행의 실제 캡처에서 하단 근거 패널을 확대',657);
  }
  {
    const s=await page(presentation,'최신 피싱 분석 실행 결과','2026-11-18 공유 완료한261118_0126latest.html을 Windows에서 정적으로 검사했다. PDF100편을 인계·검증했고 R1은30편을 선정했다. 노드421, 간선419, 간선별 근거 패널419개를 확인했다. 419개의 고유 방향 간선과419개의 근거 패널의 키가 모두 일치했다. 헤르메스는 Ubuntu에서 실제 포인터로 R1→R2및R2→R3간선 클릭을 검증했다. Windows에서의 직접 UI 재검수는 로컬 파일 접근 정책으로 수행하지 못했다.',[`${root}/reports/phishing_windows_handoff_20261118/README.md`,'reports/phishing_windows_handoff_20261118/graph.html']);
    text(s,'100편 PDF 인계 후 30편을 출발 논문으로 선정',52,124,1176,52,31,true,blue);
    table(s,[['확인 항목','최신 결과'],['인용 그래프','421개 논문 노드 / 419개 방향 간선'],['간선 근거 패널','419개 방향쌍 모두 연결'],['출발 논문 보존','선정한 R1 30편 모두 표시'],['출판연도 확인','전체 그래프 421노드 중 170개'],['파일 공유','Ubuntu 원본과 Windows 공유본 해시 일치']],52,211,1176,340,[380,796],25);
    text(s,'검수 과정에서 잘린 DOI, 자기간선 집계, 누락된 R1 노드를 보정',52,581,1176,62,25,false,gray);
  }
  {
    const s=await page(presentation,'최신 문맥 점수 분포와 남은 검토','표시 간선419개의 분포는 소개310, 보류77, 비교22, 한계10, 채택0이다. 채택0은 이번 분석에서 확정된 채택 분류가0건임을 뜻한다. 분야 전체에 채택 인용이 없다고 해석하지 않는다. 고립 R1 11편은 이번 문맥 추출 원장에 기록된 인용 문맥이0건이었으므로 실제 참고문헌이 없다는 뜻으로 해석하지 않는다. 자동 분류의 정확도는 별도 평가가 남아 있다.',[`${root}/reports/phishing_windows_handoff_20261118/README.md`,'reports/phishing_windows_handoff_20261118/graph.html']);
    table(s,[['문맥 분류','점수','간선 수'],['소개','+0.5','310'],['판정 보류','+0.2','77'],['비교·검증','+0.5','22'],['한계 지적','−0.5','10'],['채택·발전','+1.5','0'],['합계','','419']],52,135,612,435,[292,130,190],24);
    text(s,'남은 검토',716,151,500,42,29,true,blue);
    text(s,'보류 77건의 본문·인용 목적 확인\n\n고립 R1 11편의 추출 누락 원인 점검\n\n문맥 자동 분류의 사람 검토',716,221,488,310,25);
    sourceLine(s,'현재 표본에서 채택으로 확정한 인용은 0건   분류 정확도 평가는 후속 과제',616);
  }
  {
    const s=await page(presentation,'매개중심성으로 찾은 중간 논문 후보','최신HTML에 포함된 ANALYTICS의 node_metrics.betweenness를 내림차순으로 읽었다. 아래 순위는 확정된421노드419간선의 구조에 한정한다. 내용상 기반·발전·매개 역할은 개별 원문으로 검토해야 한다. 표는 상위3편의 원문 제목을 그대로 보존하고 소수점6자리 점수를 표시했다.',[source.citracer,'reports/phishing_windows_handoff_20261118/graph.html']);
    table(s,[['후보 논문','매개중심성'],...result.top.slice(0,3).map(v=>[v.title,v.betweenness.toFixed(6)])],52,155,1176,340,[960,216],24);
    text(s,'다음 확인',52,543,240,44,29,true,blue);
    text(s,'각 후보의 앞뒤 인용 문맥을 읽고 연결한 연구 방법과 역할을 설명',300,543,914,76,26);
    sourceLine(s,'2026.11.18 최종 그래프의 구조상 후보 순위');
  }
  {
    const s=await page(presentation,'활용 도구와 출처','NetMiner는 스터디와 실습에 사용한 상용 네트워크 분석 도구다. 실제 프로젝트의 그래프 렌더러와 매개중심성 계산에는 citracer와 NetworkX를 사용했다. citracer는marcpinet의MIT오픈소스이며 프로젝트에서 문맥 패널·가감점 규칙·깊이순 기본 배치를 연결했다. OpenAI Codex는 코드 구현, 오류 수정, 검수와 발표자료 작성에 활용했다. Ubuntu의모든 문맥 판정이OpenAI API호출로 이루어졌다는 근거는 확인하지 않았으므로 그런 주장을 하지 않는다. 점수 규칙은 사용자와 합의한 프로젝트 규칙이다. 로고는 공식SVG원본을 비율 유지해 사용했다.',Object.values(source));
    table(s,[['도구·자료','활용 내용','출처'],['NetMiner','중심성 분석 스터디와 실습','netminer.com/kr'],['citracer / MIT','인용망 분석과 HTML 렌더링','github.com/marcpinet/citracer'],['NetworkX','방향성 매개중심성 계산','networkx.org'],['OpenAI Codex','구현·오류 수정·검수·발표자료 작성 지원','openai.com/codex'],['인용 문맥 배점','사용자와 합의한 가감점 규칙','CITATION_CONTEXT_RULES.md'],['KGU 공식 로고','공식 SVG 원본을 비율 유지해 삽입','kyonggi.ac.kr UI 안내']],52,129,1176,415,[270,506,400],22);
    text(s,'프로젝트   github.com/sonamoo0407/paper',52,579,1176,42,26,true,blue);
    sourceLine(s,'각 슬라이드 발표자 노트에 원본 URL과 실제 실행 자료 위치 기록',631);
  }
  return {slideCount:presentation.slides.items.length};
}
