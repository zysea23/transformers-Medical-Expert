export const checkNull = (value) => {
  return value ? value : "--";
};

export const convertDate = (dateString) => {
  if (!dateString) return "--";
  const options = { year: "numeric", month: "long", day: "numeric" };
  return new Date(dateString).toLocaleDateString(undefined, options);
};
