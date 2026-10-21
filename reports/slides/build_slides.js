const pptxgen = require("pptxgenjs");
const pres = new pptxgen(); pres.layout = "LAYOUT_16x9"; pres.title = "EcoDrive";
const F = "Calibri", T = "8FB8FF", TX = "E6E9EF", G = "9AA3B2", BG = "1E2330", LINE = "3A4150";
let n = 0;
function slide(titre, qui) {
  const s = pres.addSlide(); n++; s.background = { color: BG };
  s.addText(titre, { x: 0.5, y: 0.3, w: 9, h: 0.6, fontFace: F, fontSize: 26, bold: true, color: T, margin: 0 });
  s.addText(`EcoDrive – ${qui}`, { x: 0.5, y: 5.2, w: 6, h: 0.3, fontFace: F, fontSize: 9, color: G, margin: 0 });
  s.addText(String(n), { x: 9.1, y: 5.2, w: 0.4, h: 0.3, fontFace: F, fontSize: 9, color: G, align: "right", margin: 0 });
  return s;
}
const puces = (s, l, o) => s.addText(l.map((t, i) => ({ text: t.replace(/^> /, ""), options: { bullet: t.startsWith("> ") ? { indent: 15 } : true, indentLevel: t.startsWith("> ") ? 1 : 0, breakLine: i < l.length - 1 } })),
  Object.assign({ fontFace: F, fontSize: 15, color: TX, margin: 0, valign: "top", paraSpaceAfter: 8 }, o));
const axes = { catAxisLabelFontFace: F, valAxisLabelFontFace: F, catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
  catAxisLabelColor: TX, valAxisLabelColor: G, valGridLine: { color: LINE, size: 0.5 }, catGridLine: { style: "none" } };

// 1
{ const s = pres.addSlide(); n++; s.background = { color: BG };
  s.addText("EcoDrive", { x: 0.5, y: 1.5, w: 9, h: 0.9, fontFace: F, fontSize: 40, bold: true, color: T, margin: 0 });
  s.addText("Prédire la consommation de carburant d'une flotte de véhicules", { x: 0.5, y: 2.4, w: 9, h: 0.5, fontFace: F, fontSize: 20, color: TX, margin: 0 });
  s.addText("Enzo BASLY – Guillaume – Rayan", { x: 0.5, y: 3.7, w: 9, h: 0.8, fontFace: F, fontSize: 14, color: G, margin: 0 });
  s.addNotes("ENZO (10 s) : Bonjour, on va vous présenter EcoDrive, un modèle qui prédit la consommation de carburant d'une flotte de véhicules."); }

// 2
{ const s = slide("Le problème", "Enzo");
  puces(s, ["Client : une entreprise avec 100 véhicules de service",
    "Chaque lundi, le gestionnaire doit décider :", "> quels véhicules envoyer au garage (consomment trop)", "> quels conducteurs former à l'éco-conduite",
    "Aujourd'hui : il compare juste à la conso moyenne du véhicule",
    "Notre question : quelle consommation est normale pour ce trajet ?", "> régression, cible = L/100 km du trajet"], { x: 0.5, y: 1.3, w: 9, h: 3.7, fontSize: 18 });
  s.addNotes("ENZO (1 min) : On s'est mis à la place d'une entreprise qui a 100 voitures de service. Chaque semaine le gestionnaire doit savoir quelles voitures envoyer au garage et quels conducteurs former. Aujourd'hui il compare juste à la moyenne du véhicule, donc il ne sait pas si une voiture consomme trop à cause d'un défaut ou juste parce qu'elle a fait de la ville. On a choisi une régression : on prédit la conso normale d'un trajet, et si la conso réelle est bien au-dessus, il y a un problème. On n'a pas fait de classification parce qu'aucun défaut n'est noté dans les données."); }

// 3
{ const s = slide("Les données", "Enzo");
  puces(s, ["Vehicle Energy Dataset (VED, université du Michigan, 2020)",
    "Capteurs OBD des voitures : vitesse, régime, température…",
    "On regroupe les mesures par trajet : 2 175 trajets, 85 véhicules",
    "On retire les trajets < 1 km et les valeurs impossibles",
    "Variables écartées (fuite) : débit d'air et débit carburant, car ils servent à calculer la cible"], { x: 0.5, y: 1.3, w: 9, h: 3.7, fontSize: 18 });
  s.addNotes("ENZO (1 min) : On a utilisé le dataset VED, ce sont des vraies mesures de voitures enregistrées pendant un an. Les capteurs donnent une ligne toutes les secondes, donc on a tout regroupé par trajet. On a enlevé les trajets trop courts. Point important : on n'a pas gardé le débit d'air ni le débit carburant comme variables, parce que c'est avec eux qu'on calcule la consommation, ça aurait été donner la réponse au modèle. Je laisse Guillaume pour les modèles."); }

// 4
{ const s = slide("Les modèles testés", "Guillaume");
  s.addChart(pres.charts.BAR, [{ name: "MAE", labels: ["Moyenne globale", "Règle actuelle", "Arbre simple", "Régression linéaire", "Gradient Boosting", "Random Forest"], values: [2.02, 1.16, 0.86, 0.75, 0.67, 0.66] }],
    Object.assign({ x: 0.4, y: 1.1, w: 5.6, h: 3.9, barDir: "bar", chartColors: ["5B9BD5"], showValue: true, dataLabelFontSize: 10, dataLabelFormatCode: "0.00",
      showLegend: false, showTitle: true, title: "Erreur moyenne en validation (L/100 km)", titleFontSize: 12, titleFontFace: F, titleColor: TX, dataLabelColor: TX, legendColor: TX }, axes));
  puces(s, ["Train = trajets les plus anciens, test = les plus récents",
    "Préparation dans un pipeline", "Validation croisée sur 5 périodes",
    "Plus l'erreur est basse, mieux c'est"], { x: 6.2, y: 1.3, w: 3.4, h: 3.6, fontSize: 13 });
  s.addNotes("GUILLAUME (1 min 10) : On a coupé les données dans l'ordre du temps : on apprend sur les premiers mois et on teste sur les derniers, comme en vrai. Toute la préparation est dans un pipeline pour ne pas tricher avec les données de test. On a comparé 6 modèles avec une validation croisée. La Random Forest fait le moins d'erreur. L'arbre simple apprenait par cœur : erreur zéro sur l'entraînement mais moins bon en validation."); }

// 5
{ const s = slide("Résultat sur le test", "Guillaume");
  s.addChart(pres.charts.BAR, [{ name: "Erreur", labels: ["Règle actuelle", "Notre modèle"], values: [1.27, 0.72] }],
    Object.assign({ x: 0.4, y: 1.1, w: 4.6, h: 3.9, barDir: "col", chartColors: ["7F8794", "5B9BD5"], showValue: true, dataLabelFontSize: 12, dataLabelFormatCode: "0.00",
      showLegend: false, showTitle: true, title: "Erreur moyenne sur le test (L/100 km)", titleFontSize: 12, titleFontFace: F, titleColor: TX, dataLabelColor: TX, legendColor: TX }, axes));
  puces(s, ["Erreur divisée par presque 2", "62 % des trajets prédits à moins de 10 % près",
    "Ce qui compte le plus : le véhicule, puis le régime moteur, les accélérations et le froid"], { x: 5.3, y: 1.3, w: 4.3, h: 3.6 });
  s.addNotes("GUILLAUME (1 min 10) : Sur les trajets du test, que le modèle n'avait jamais vus, il se trompe en moyenne de 0,72 litre aux 100, contre 1,27 pour la méthode actuelle. Les variables les plus importantes sont logiques : le type de véhicule, le régime moteur, les accélérations et la température. Je laisse Rayan pour ce qu'on en fait concrètement."); }

// 6
{ const s = slide("Alertes et styles de conduite", "Rayan");
  s.addChart(pres.charts.BAR, [
    { name: "Calme", labels: ["Autoroute", "Mixte", "Ville"], values: [8.18, 6.74, 7.14] },
    { name: "Normal", labels: ["Autoroute", "Mixte", "Ville"], values: [8.80, 6.69, 7.77] },
    { name: "Nerveux", labels: ["Autoroute", "Mixte", "Ville"], values: [9.70, 7.61, 8.81] }],
    Object.assign({ x: 0.4, y: 1.1, w: 5.2, h: 3.9, barDir: "col", chartColors: ["70AD47", "FFC000", "E05555"], showLegend: true, legendPos: "b", legendFontSize: 10,
      showTitle: true, title: "Conso moyenne par style (L/100 km)", titleFontSize: 12, titleFontFace: F, titleColor: TX, dataLabelColor: TX, legendColor: TX }, axes));
  puces(s, ["Conduite nerveuse : +13 à +23 % de conso à trajet égal",
    "Alerte si un véhicule consomme +15 % de plus que prévu sur ses 10 derniers trajets",
    "96 % des défauts simulés détectés, mais 5,8 fausses alertes par semaine"], { x: 5.8, y: 1.3, w: 3.8, h: 3.7, fontSize: 13 });
  s.addNotes("RAYAN (1 min 10) : Le modèle sert à deux choses. D'abord comparer les styles : à trajet égal, quelqu'un qui conduit nerveux consomme 13 à 23 % de plus. Ensuite les alertes : si une voiture consomme 15 % de plus que prévu sur ses 10 derniers trajets, on l'envoie au garage. Comme il n'y a pas de pannes notées dans les données, on a ajouté des faux défauts pour tester. On en trouve 96 %, mais il y a encore trop de fausses alertes, presque 6 par semaine."); }

// 7
{ const s = slide("Combien ça rapporte ?", "Rayan");
  s.addTable([["", "Gain / an", "Coût an 1", "ROI 3 ans"],
    ["Pessimiste", "-875 €", "10 800 €", "-112 %"], ["Central", "6 130 €", "10 800 €", "-15 %"],
    ["Optimiste", "9 157 €", "10 800 €", "+27 %"], ["Flotte à 30 000 km/an", "9 680 €", "10 800 €", "+34 %"]].map((r, i) => r.map(v => ({ text: v,
      options: i === 0 ? { bold: true, color: BG, fill: { color: T } } : { color: TX, fill: { color: "262C3A" } } }))),
    { x: 0.5, y: 1.2, w: 5.4, colW: [2.1, 1.1, 1.1, 1.1], fontFace: F, fontSize: 12, border: { type: "solid", pt: 0.5, color: LINE }, rowH: 0.4 });
  puces(s, ["Rentable seulement si les conducteurs changent vraiment leur conduite, et pour les flottes qui roulent beaucoup",
    "Recommandation : un test de 3 mois sur 20 véhicules avant de déployer"], { x: 6.2, y: 1.2, w: 3.4, h: 3.7, fontSize: 13 });
  s.addText("Merci, avez-vous des questions ?", { x: 0.5, y: 4.3, w: 5.4, h: 0.5, fontFace: F, fontSize: 16, bold: true, color: T, margin: 0 });
  s.addNotes("RAYAN (1 min 10) : Pour 100 véhicules, on gagne environ 6 000 euros par an en carburant, pour un coût de 10 800 euros la première année. Dans le scénario central ce n'est pas encore rentable sur 3 ans, ça le devient si les conducteurs changent vraiment leur conduite ou si la flotte roule beaucoup. Donc on recommande un test de 3 mois sur 20 véhicules pour mesurer l'économie réelle avant de déployer. Merci, on est prêts pour vos questions."); }

pres.writeFile({ fileName: "/home/claude/court/Soutenance_EcoDrive_7min.pptx" }).then(f => console.log("OK", f));
