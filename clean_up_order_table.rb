require 'json'

input_file = ARGV[0]
output_file = input_file.gsub('.json', '-cleansed.json').gsub(/.*\//, '')

def x_out_name(hash)
  hash.transform_values do |v|
    if v['name'] == 'Supercoop'
      v
    else
      v.merge({'name' => 'XXX'})
    end
  end
end

orders = JSON.parse(File.read(input_file))
cleansed_orders = orders["values"].map do |order|
  order.map do |attribute|
    if attribute.is_a?(Hash)
      attribute.merge({ 'members'=> x_out_name(attribute['members']) })
    else
      attribute
    end
  end
end

File.write(output_file, cleansed_orders.to_json)
