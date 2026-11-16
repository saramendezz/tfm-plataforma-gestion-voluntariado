const CATEGORY_LABELS = {
  health: "Sanitaria",
  logistics: "Logística y transporte",
  technical: "Técnica y oficios",
  communication: "Comunicación e idiomas",
  social: "Atención y acompañamiento",
  coordination: "Coordinación",
};

export default function SkillPicker({ skills, value, onChange }) {
  const grouped = skills.reduce((acc, skill) => {
    (acc[skill.category] ||= []).push(skill);
    return acc;
  }, {});

  function toggle(id) {
    onChange(value.includes(id) ? value.filter((v) => v !== id) : [...value, id]);
  }

  return (
    <>
      {Object.entries(grouped).map(([category, list]) => (
        <fieldset key={category}>
          <legend>{CATEGORY_LABELS[category] ?? category}</legend>
          {list.map((skill) => (
            <label key={skill.id} className="inline">
              <input
                type="checkbox"
                checked={value.includes(skill.id)}
                onChange={() => toggle(skill.id)}
              />
              {skill.name}
            </label>
          ))}
        </fieldset>
      ))}
    </>
  );
}