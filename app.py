from flask import Flask, render_template_string, request, redirect, url_for
import urllib.parse
import requests


app = Flask(__name__)

STATE_LIST = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
    "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
    "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico",
    "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
    "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
]

HTML_TEMPLATE = """
<!doctype html>
<title>OSM Query Interface</title>
<style>
  body {
    padding-left: 40px;
    font-family: sans-serif;
  }
  #queries {
    margin-top: 20px;
  }
  .query {
    margin-bottom: 12px;
  }
</style>
<h2>Query the Open Map Database</h2>
<form method="post" action="{{ url_for('search') }}">
  <label for="state">Select a State:</label>
  <select name="state" id="state">
    {% for state in states %}
    <option value="{{ state }}" {% if selected_state == state %}selected{% endif %}>{{ state }}</option>
    {% endfor %}
  </select>
  <div id="queries">
    {% for name, amenity, distance in query_inputs %}
    <div class="query">
      <input name="name[]" placeholder="Node/Way Name" value="{{ name }}">
      <select name="amenity[]">
        <option value="fast_food" {% if amenity == "fast_food" %}selected{% endif %}>fast_food</option>
        <option value="restaurant" {% if amenity == "restaurant" %}selected{% endif %}>restaurant</option>
        <option value="cafe" {% if amenity == "cafe" %}selected{% endif %}>cafe</option>
        <option value="bank" {% if amenity == "bank" %}selected{% endif %}>bank</option>
        <option value="school" {% if amenity == "school" %}selected{% endif %}>school</option>
        <option value="hospital" {% if amenity == "hospital" %}selected{% endif %}>hospital</option>
        <option value="police" {% if amenity == "police" %}selected{% endif %}>police</option>
        <option value="fire_station" {% if amenity == "fire_station" %}selected{% endif %}>fire_station</option>
        <option value="parking" {% if amenity == "parking" %}selected{% endif %}>parking</option>
        <option value="fuel" {% if amenity == "fuel" %}selected{% endif %}>fuel</option>
        <option value="post_office" {% if amenity == "post_office" %}selected{% endif %}>post_office</option>
        <option value="library" {% if amenity == "library" %}selected{% endif %}>library</option>
        <option value="pharmacy" {% if amenity == "pharmacy" %}selected{% endif %}>pharmacy</option>
        <option value="bar" {% if amenity == "bar" %}selected{% endif %}>bar</option>
        <option value="pub" {% if amenity == "pub" %}selected{% endif %}>pub</option>
        <option value="toilets" {% if amenity == "toilets" %}selected{% endif %}>toilets</option>
        <option value="place_of_worship" {% if amenity == "place_of_worship" %}selected{% endif %}>place_of_worship</option>
      </select>
      <input name="distance[]" placeholder="Distance (optional)" value="{{ distance }}">
      <button type="button" onclick="this.parentElement.remove()">Remove</button>
    </div>
    {% endfor %}
    {% if not query_inputs %}
    <div class="query">
      <input name="name[]" placeholder="Node/Way Name">
      <select name="amenity[]">
        <option value="fast_food">fast_food</option>
        <option value="restaurant">restaurant</option>
        <option value="cafe">cafe</option>
        <option value="bank">bank</option>
        <option value="school">school</option>
        <option value="hospital">hospital</option>
        <option value="police">police</option>
        <option value="fire_station">fire_station</option>
        <option value="parking">parking</option>
        <option value="fuel">fuel</option>
        <option value="post_office">post_office</option>
        <option value="library">library</option>
        <option value="pharmacy">pharmacy</option>
        <option value="bar">bar</option>
        <option value="pub">pub</option>
        <option value="toilets">toilets</option>
        <option value="place_of_worship">place_of_worship</option>
      </select>
      <input name="distance[]" placeholder="Distance (optional)">
      <button type="button" onclick="this.parentElement.remove()">Remove</button>
    </div>
    {% endif %}
  </div>
  <button type="button" onclick="addQuery()">Add Another Query</button>
  <button type="submit">Go</button>
</form>

{% if generated_query %}
<h3>Generated Query</h3>
<pre>{{ generated_query }}</pre>
{% endif %}

{% if results %}
<h3>Results</h3>
<ul>
  {% for r in results %}
  <li>{{ r|safe }}</li>
  {% endfor %}
</ul>
{% endif %}

<script>
const amenitySelectHtml = `<select name="amenity[]">
  <option value="fast_food">fast_food</option>
  <option value="restaurant">restaurant</option>
  <option value="cafe">cafe</option>
  <option value="bank">bank</option>
  <option value="school">school</option>
  <option value="hospital">hospital</option>
  <option value="police">police</option>
  <option value="fire_station">fire_station</option>
  <option value="parking">parking</option>
  <option value="fuel">fuel</option>
  <option value="post_office">post_office</option>
  <option value="library">library</option>
  <option value="pharmacy">pharmacy</option>
  <option value="bar">bar</option>
  <option value="pub">pub</option>
  <option value="toilets">toilets</option>
  <option value="place_of_worship">place_of_worship</option>
</select>`;
function addQuery() {
  const container = document.getElementById('queries');
  const div = document.createElement('div');
  div.classList.add('query');
  div.innerHTML = '<input name="name[]" placeholder="Node/Way Name"> ' + amenitySelectHtml + ' <input name="distance[]" placeholder="Distance (optional)"> <button type="button" onclick="this.parentElement.remove()">Remove</button>';
  container.appendChild(div);
  div.querySelector('input[name="name[]"]').focus();
}
</script>
"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(
        HTML_TEMPLATE,
        states=STATE_LIST,
        selected_state="Tennessee",
        query_inputs=[],
        results=None,
        generated_query=None
    )

@app.route('/search', methods=['POST'])
def search():
    state = request.form.get('state')
    names = request.form.getlist('name[]')
    amenities = request.form.getlist('amenity[]')
    distances = request.form.getlist('distance[]')
    query_inputs = list(zip(names, amenities, distances))

    query = '[out:json][timeout:60];\n'
    query += f'area["name"="{state}"]["admin_level"="4"]->.searchArea;\n'

    refs = []
    for i, (name, amenity, dist) in enumerate(query_inputs):
        ref = f'.step{i}'
        name_filter = f'["name"="{name}"]' if name.strip() else ''
        if i == 0:
            query += f'nw["amenity"="{amenity}"]{name_filter}(area.searchArea)->{ref};\n'
        else:
            parent = refs[-1]
            query += f'nw(around{parent}:{dist})["amenity"="{amenity}"]{name_filter}->{ref};\n'
        refs.append(ref)

    query += f'({refs[-1]};);\nout center;'

    response = requests.post("https://overpass-api.de/api/interpreter", data=query)
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        return render_template_string(
            HTML_TEMPLATE,
            states=STATE_LIST,
            selected_state=state,
            query_inputs=query_inputs,
            results=["Error: Failed to parse response from Overpass API."],
            generated_query=query
        )

    results = []
    for el in data.get('elements', []):
        lat = el.get('lat') or el.get('center', {}).get('lat')
        lon = el.get('lon') or el.get('center', {}).get('lon')
        name = el.get('tags', {}).get('name', 'Unknown')
        if lat and lon:
            map_url = f"https://www.google.com/maps?q={lat},{lon}"
            results.append(f"{name}: <a href='{map_url}' target='_blank'>Map Link</a>")

    if not results:
        results.append("No results found.")

    return render_template_string(
        HTML_TEMPLATE,
        states=STATE_LIST,
        selected_state=state,
        query_inputs=query_inputs,
        results=results,
        generated_query=query
    )

if __name__ == '__main__':
    app.run(debug=True)