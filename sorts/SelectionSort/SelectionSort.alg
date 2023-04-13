// Сортировка выбором
// Массив данных из size чисел
// Размер каждого из этих чисел - 1 байт

define size 6;
define log_size 4;
define n 4;

__in bit data[size][n];

__out bit sorted_data[size][n];

void main()
{
	for(int i = 0; i < size - 1; i = i + 1)
	{
		bit min[log_size] = i;
		for(int j = i + 1; j < size; j = j + 1)
		{
			// if(data[j] < data[min]) min = j;
			for(int k = i; k < size; k = k + 1)
			{
				if((min == k) & (data[j] < data[k]))
				{
					min = j;
				}
			}
		}
		// std::swap(data[i], data[min]);
		for(int k = i; k < size; k = k + 1)
		{
			if(min == k)
			{
				bit t[n] = data[i];
				data[i] = data[k];
				data[k] = t;
			}
		}
	}

	sorted_data = data;
}
