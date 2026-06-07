export interface Crop {
  value: string;
  label: string;
  icon: string;
}

export const CROPS: Crop[] = [
  { value: "wheat", label: "Wheat / Gehu", icon: "\uD83C\uDF3E" },
  { value: "rice", label: "Rice / Chawal", icon: "\uD83C\uDF5A" },
  { value: "tomato", label: "Tomato / Tamatar", icon: "\uD83C\uDF45" },
  { value: "onion", label: "Onion / Pyaaz", icon: "\uD83E\uDDC5" },
  { value: "potato", label: "Potato / Aloo", icon: "\uD83E\uDD54" },
  { value: "cotton", label: "Cotton / Kapas", icon: "\u2601\uFE0F" },
  { value: "sugarcane", label: "Sugarcane / Ganna", icon: "\uD83C\uDF6C" },
  { value: "maize", label: "Maize / Makka", icon: "\uD83C\uDF3D" },
  { value: "soyabean", label: "Soyabean / Soya", icon: "\uD83E\uDED8" },
];

export const CROP_VALUES = CROPS.map((c) => c.value);

export const CITIES = [
  "Delhi",
  "Mumbai",
  "Kolkata",
  "Chennai",
  "Bangalore",
  "Hyderabad",
  "Pune",
  "Ahmedabad",
  "Jaipur",
  "Lucknow",
];
